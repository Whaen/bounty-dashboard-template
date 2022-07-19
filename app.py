import streamlit as st
import yaml, requests, re, os, json
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode, JsCode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_echarts import st_echarts

class payout_calculator():
    """
        Calculate the total flipside payout from README.md, and tabulate it based on blockchains category
    """
    def __init__(self, yml_f, trk_f):
        self.curr_chain = None 
        self.curr_year  = None
        self.decode_yaml(yml_f)
        d = self.parse_in_f(trk_f)
        df = self.dataframe(d)
        if os.path.isdir('data') == False:
            os.mkdir('data')
        df.to_csv('data/payout.csv', encoding='utf-8', index=False)

    def decode_yaml(self, yml_f):
        with open(yml_f, 'r') as stream:
            try:
                self.parsed_yaml = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print (exc)

    def parse_in_f(self, trk_f):
        self.blockchain_lst = list(self.parsed_yaml['blockchain-list'].keys())
        years = self.parsed_yaml['year']
        d = dict()
        for year in years:
            d[year] = {}
            for chain in self.blockchain_lst:
                d[year][chain] = {}
                for denom in self.parsed_yaml['blockchain-list'][chain]:
                    d[year][chain][denom] = {}
                    d[year][chain][denom]['amount'] = 0
                    d[year][chain][denom]['price'] = self.get_price(self.parsed_yaml['API'][denom])
        
        # Read line by line
        with open(trk_f, 'r', encoding="utf8") as fp:
            for line in fp:
                # set current chain
                for n in range(0, len(self.blockchain_lst)):
                    if re.match(f".+{self.blockchain_lst[n]} Bounties+.", line):
                        self.curr_chain = self.blockchain_lst[n]
             
                # set current year
                for n in range(0, len(years)):
                    if re.match(f"^## +{years[n]}", line):
                        self.curr_year = years[n]
                
                # the rest of the README's table element
                if re.match(f"^\|.(✅)", line):
                    for denom in self.parsed_yaml['blockchain-list'][self.curr_chain]:
                        payout = re.findall(f"((\d+\.\d+)|\d+)(?=\s*{denom})", line)
                        if len(payout) != 0:
                            value = float(payout[0][0])
                            d[self.curr_year][self.curr_chain][denom]['amount'] += value
        return d
    
    def dataframe(self, d):
        data = list()
        for year in d.keys():
            for chain in self.blockchain_lst:
                for denom in self.parsed_yaml['blockchain-list'][chain]:
                    data.append([year, chain, denom, d[year][chain][denom]['amount'], "{:.2f}".format(d[year][chain][denom]['price']), "{:.2f}".format(d[year][chain][denom]['amount']*d[year][chain][denom]['price'])])
        df = pd.DataFrame(data,columns=['Year','Blockchain','Tokens','Amount','Price','Amount_USD'])
        return df

    def get_price(self, token, currency = 'usd'):
        api_url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency={currency}&ids={token.lower()}"
        response = requests.get(api_url)
        if response.status_code == 200:
            get_result = response.json()
            if len(get_result) != 0:
                current_price = get_result[0]['current_price'] # in usd
            else:
                current_price = 0
        else: current_price = 0
        return current_price

# ---- STREAMLIT RENDER ---- #
def streamlit_render():
    # ---- CONFIGURATION ----
    ## --- all container ---
    header = st.container()
    metric_card = st.container()
    horizon_bar = st.container()
    year_chart = st.container()
    sub_header = st.container()
    data_table = st.container()
    ## --- all container ---

    ## Load style.css
    with open("cfg/style.css") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    ## Read csv from a
    @st.experimental_memo
    def get_data(dataset=r"data/payout.csv"):
        return pd.read_csv(dataset)
    df = get_data()
    # ---- CONFIGURATION ----

    # ---- Header TEXT ----
    with header:
        st.markdown('<h1 style="text-align:center"><img src="https://i.imgur.com/pyasxls.png" alt="logo" height="60">&nbsp Flipside Income Dashboard </h1>', unsafe_allow_html=True)
    # ---- Header TEXT ----

    # ---- Metric Card ---- Yearly Total Earn
    with metric_card:
        yearly_sum = df.groupby("Year")["Amount_USD"].sum().sort_values()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", "$"+"{:.2f}".format(yearly_sum.sum())+" USD", None) 
        col2.metric("2021", "$"+"{:.2f}".format(yearly_sum.loc[2021])+" USD", None) 
        col3.metric("2022", "$"+"{:.2f}".format(yearly_sum.loc[2022])+" USD", None)
        # spacing 
        st.markdown(r'''
            #
        ''')
    # ---- Metric Card ----

    # ---- HORIZONTAL BAR ----
    with horizon_bar:
        gb_blockchain = (df.groupby("Blockchain", as_index = False).sum()).sort_values('Amount_USD')
        col1, col2=st.columns(2)
        # Pie Chart  
        with col1:
            name = list(gb_blockchain['Blockchain'])
            value = list(gb_blockchain['Amount_USD'])
            wrap_bar = list()
            for i in range(0,len(name)):
                wrap_bar.append({"value": value[i], "name": name[i]})
            pie_options = {
                "title": {
                    "text": "Total Income USD Slices",
                    "left": "center",
                    "top": 5,
                    "textStyle": {"color": "#e6e6e6"},
                },
                "legend": {
				    "bottom": 5,
				    "left": 'center',
                    "textStyle":{
                        "color":'#E6E6E6'
                        }
			  	},
                "tooltip": {"trigger": "item", "formatter": "{a} <br/>{b} : {c} ({d}%)"},
                "series": [
				    {
				      "name": "Access From",
				      "type": "pie",
				      "radius": ["45%", "70%"],
				      "avoidLabelOverlap": False,
				      "label": {
				        "show": False,
				        "position": "center"
				      },
				      "emphasis": {
				        "label": {
				          "show": True,
				          "fontSize": "20",
				          "fontWeight": "bold"
				        }
				      },
				      "labelLine": {
				        "show": False
				      },
				      "data": wrap_bar,
                      "color": ["#0f488c", "#696cb5", "#e85e76", "#ef8a5a", "#f6b53d", "#15cab6", "#287e8f"]
				    }
				]
            }
            st_echarts(options=pie_options, height="500px")

        # Horizontal Bar Chart by Chain
        with col2:
            wrap_chain = (df.groupby(["Blockchain", "Tokens"], as_index = False).sum())
            # Prepare index for table
            index_lst = wrap_chain[['Tokens', 'Blockchain']].agg('-'.join, axis=1)
            wrap_chain.index = index_lst
            token_lst = list(wrap_chain["Tokens"].unique())
            # Prepare dataframe dict
            chain_lst = list(wrap_chain["Blockchain"].unique())
            dataframe = dict()
            for i in token_lst:
                dataframe[i] = dict()
                for j in chain_lst:
                    try:
                        if wrap_chain.loc[str(i)+'-'+str(j), 'Tokens'] == i:
                            dataframe[i][j] = wrap_chain.loc[str(i)+'-'+str(j), 'Amount_USD']
                    except:
                        dataframe[i][j] = 0
            
            eth_lst   = list(dataframe['ETH'].values())
            usdc_lst  = list(dataframe['USDC'].values())
            near_lst  = list(dataframe['NEAR'].values())
            osmo_lst  = list(dataframe['OSMO'].values())
            matic_lst = list(dataframe['MATIC'].values())
            sol_lst   = list(dataframe['SOL'].values())
            rune_lst  = list(dataframe['RUNE'].values())

            bar_options = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "title": {
                    "text": "Total Income USD by Blockchain",
                    "textStyle":{
                    "color":'#E6E6E6'
                    },
                    "left": "center",
                },
                "legend": {
                    "data": list(dataframe.keys()),
                    "textStyle":{
                        "color":'#E6E6E6'
                    },
                    "bottom": 5,
				    "left": 'center',
                },
                "grid": {"left": "3%", "right": "4%", "bottom": "10%", "containLabel": True},
                "xAxis": {
                    "type": "value",
                    "axisLabel": {
                            "textStyle": {
                                "color": '#E6E6E6'
                            }
                        }
                },
                "yAxis": {
                    "type": "category",
                    "data": list(dataframe['ETH'].keys()),
                    "axisLabel": {
                            "textStyle": {
                                "color": '#E6E6E6'
                            }
                        }
                },
                "series": [
                    {
                        "name": "ETH",
                        "type": "bar",
                        "stack": "total",
                        "label": {"show": True},
                        "emphasis": {"focus": "series"},
                        "data": eth_lst,
                        "color": '#287e8f',
                        "emphasis": {"focus": 'series'}
                    },
                    {
                        "name": "USDC",
                        "type": "bar",
                        "stack": "total",
                        "label": {"show": True},
                        "emphasis": {"focus": "series"},
                        "data": usdc_lst,
                        "color": '#15cab6',
                        "emphasis": {"focus": 'series'}
                    },
                    {
                        "name": "NEAR",
                        "type": "bar",
                        "stack": "total",
                        "label": {"show": True},
                        "emphasis": {"focus": "series"},
                            
                        "emphasis": {"focus": 'series'}
                    },
                    {
                        "name": "OSMO",
                        "type": "bar",
                        "stack": "total",
                        "label": {"show": True},
                        "emphasis": {"focus": "series"},
                        "data": osmo_lst,
                        "color": '#ef8a5a',
                        "emphasis": {"focus": 'series'}
                    },
                    {
                        "name": "MATIC",
                        "type": "bar",
                        "stack": "total",
                        "label": {"show": True},
                        "emphasis": {"focus": "series"},
                        "data": matic_lst,
                        "color": '#e85e76',
                        "emphasis": {"focus": 'series'}
                    },
                    {
                        "name": "SOL",
                        "type": "bar",
                        "stack": "total",
                        "label": {"show": True},
                        "emphasis": {"focus": "series"},
                        "data": sol_lst,
                        "color": '#696cb5',
                        "emphasis": {"focus": 'series'}
                    },
                    {
                        "name": "RUNE",
                        "type": "bar",
                        "stack": "total",
                        "label": {"show": True},
                        "emphasis": {"focus": "series"},
                        "data": rune_lst,
                        "color": '#0f488c',
                        "emphasis": {"focus": 'series'}
                    },
                ],
            }
            st_echarts(options=bar_options, height="500px")
    
    
    with year_chart:
        col1, col2=st.columns(2)
        # Bar Chart By Years
        with col1:
            wrap_chain = (df.groupby(["Year", "Blockchain"], as_index = False).sum())
            # Prepare index for table
            index_lst = list(wrap_chain['Blockchain']+"-"+wrap_chain['Year'].astype(str))
            wrap_chain.index = index_lst
            chain_lst = list(wrap_chain["Blockchain"].unique())
            # Prepare dataframe dict
            year_lst = list(wrap_chain["Year"].unique())
            dataframe = dict()
            for i in chain_lst:
                dataframe[i] = dict()
                for j in year_lst:
                    try:
                        if wrap_chain.loc[str(i)+'-'+str(j), 'Blockchain'] == i:
                            dataframe[i][j] = wrap_chain.loc[str(i)+'-'+str(j), 'Amount_USD']
                    except:
                        dataframe[i][j] = 0
            
            eth_lst   = list(dataframe['ETHEREUM'].values())
            near_lst  = list(dataframe['NEAR-CHAIN'].values())
            osmo_lst  = list(dataframe['OSMOSIS'].values())
            matic_lst = list(dataframe['POLYGON'].values())
            sol_lst   = list(dataframe['SOLANA'].values())
            rune_lst  = list(dataframe['THORCHAIN'].values())

            year_lst = list(str(k) for k in dataframe["ETHEREUM"].keys())

            option = {
                "tooltip": {
                    "trigger": "axis",
                    "axisPointer": {
                    "type": "shadow"
                    }
                },
                "title": {
                    "text": "Total Income USD by Years",
                    "textStyle":{
                    "color":'#E6E6E6'
                    },
                    "left": "center",
                },
                "legend": {
                    "textStyle":{
                        "color":'#E6E6E6'
                    },
                    "bottom": 5,
                    "left": 'center',
                    "data": list(dataframe.keys())
                },
                "toolbox": {
                    "show": True,
                    "orient": "vertical",
                    "left": "right",
                    "top": "center",
                    "feature": {
                    "mark": { "show": True },
                    "dataView": { "show": True, "readOnly": False },
                    "magicType": { "show": True, "type": ["line", "bar", "stack"] },
                    "restore": { "show": True },
                    "saveAsImage": { "show": True }
                    }
                },
                "xAxis": [
                    {
                    "type": "category",
                    "axisTick": { "show": False },
                    "data": year_lst,
                    "axisLabel": {
                                "textStyle": {
                                    "color": '#E6E6E6'
                                }
                            }
                    }
                ],
                "yAxis": [
                    {
                    "axisLabel": {
                                "textStyle": {
                                    "color": '#E6E6E6'
                                }
                            },
                    "type": "value"
                    }
                ],
                "series": [
                    {
                    "name": "ETHEREUM",
                    "type": "bar",
                    "barGap": 0,
                    "label": "labelOption",
                    "emphasis": {
                        "focus": "series"
                    },
                    "color": '#287e8f',
                    "data": eth_lst
                    },
                    {
                    "name": "NEAR",
                    "type": "bar",
                    "label": "labelOption",
                    "emphasis": {
                        "focus": "series"
                    },
                    "color": '#15cab6',
                    "data": near_lst
                    },
                    {
                    "name": "OSMOSIS",
                    "type": "bar",
                    "label": "labelOption",
                    "emphasis": {
                        "focus": "series"
                    },
                    "color": '#f6b53d',
                    "data": osmo_lst
                    },
                    {
                    "name": "POLYGON",
                    "type": "bar",
                    "label": "labelOption",
                    "emphasis": {
                        "focus": "series"
                    },
                    "color": '#ef8a5a',
                    "data": matic_lst
                    },
                    {
                    "name": "SOLANA",
                    "type": "bar",
                    "label": "labelOption",
                    "emphasis": {
                        "focus": "series"
                    },
                    "color": '#e85e76',
                    "data": sol_lst
                    },
                    {
                    "name": "THORCHAIN",
                    "type": "bar",
                    "label": "labelOption",
                    "emphasis": {
                        "focus": "series"
                    },
                    "color": '#696cb5', 
                    "data": rune_lst
                    }
                ]
                }
            st_echarts(options=option, height="500px")
        
        # Sankey Diagram
        with col2:
            nodes = []
            nodes.append({'name': 'Total'})
            for y in year_lst:
                nodes.append({'name': y})
            for c in chain_lst:
                nodes.append({'name': c})
            for t in list(df["Tokens"].unique()):
                nodes.append({'name': t})
            
            links = []
            for y in year_lst:
                year = int(y)
                # total -> year
                total_year = df.groupby(["Year"], as_index = False).sum()
                total_year.index = list(total_year['Year'].astype(str))
                links.append({'source': 'Total', 'target': str(y), 'value': total_year.loc[str(y), 'Amount_USD']})
                # year -> chain
                by_year = (df.query("Year==@year").groupby(["Blockchain", "Year"], as_index = False).sum())
                by_year.index = list(by_year['Year'].astype(str)+"-"+by_year['Blockchain'])
                for c in chain_lst:
                    source = y
                    target = c 
                    value = by_year.loc[str(y)+'-'+str(c), 'Amount_USD']
                    links.append({'source': source, 'target': target, 'value': value})
                    # chain -> tokens
                    by_token = (df.query("Year==@year & Blockchain==@c"))
                    by_token.index = list(by_token['Blockchain']+"-"+by_token['Tokens'])
                    token_lst = list(by_token["Tokens"].unique())
                    for t in token_lst:
                        s_ource = c 
                        t_arget = t 
                        v_alue = by_token.loc[str(c)+'-'+str(t), 'Amount_USD']
                        links.append({'source': s_ource, 'target': t_arget, 'value': v_alue})
            
            js = {'nodes': nodes, 'links': links}
            json_data = json.loads(json.dumps(js, indent=2))
            
            option = {
                "title": {
                            "text": "Total Income Sankey",
                            "textStyle":{
                            "color":'#E6E6E6'
                            },
                            "left": "center",
                        },
                "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
                "series": [
                    {
                        "type": "sankey",
                        "data": json_data["nodes"],
                        "links": json_data["links"],
                        "emphasis": {"focus": "adjacency"},
                        "levels": [
                            {
                                "depth": 0,
                                "itemStyle": {"color": "#287e8f"},
                                "lineStyle": {"color": "source", "opacity": 0.6},
                            },
                            {
                                "depth": 1,
                                "itemStyle": {"color": "#15cab6"},
                                "lineStyle": {"color": "source", "opacity": 0.6},
                            },
                            {
                                "depth": 2,
                                "itemStyle": {"color": "#f6b53d"},
                                "lineStyle": {"color": "source", "opacity": 0.6},
                            },
                            {
                                "depth": 3,
                                "itemStyle": {"color": "#ef8a5a"},
                                "lineStyle": {"color": "source", "opacity": 0.6},
                            },
                        ],
                        "lineStyle": {"curveness": 0.5},
                    }
                ],
            }
            st_echarts(option, height="500px")
    # ---- HORIZONTAL BAR ----

    # ---- Sub-header ----
    with sub_header:
        # spacing 
        st.markdown(r'''
            #
        ''')
        st.markdown('<h2 style="text-align:center">Income Dashboard Table</h2>', unsafe_allow_html=True)
    # ---- Sub-header ----

    # ---- DATA TABLE ----
    with data_table:
        ## Filter Year
        year = st.multiselect(
            "Select the Year:",
            list(df['Year'].unique()),
            list(df['Year'].unique())
        )
        ## Filter Blockchain
        blockchain = st.multiselect(
            "Select the Blockchain:",
            list(df['Blockchain'].unique()),
            list(df['Blockchain'].unique())
        )
        ## Query the dataset based on the filter
        df_selection = df.query(
            "Year == @year & Blockchain == @blockchain"
        )
        # st.dataframe(df_selection)
        # st.sidebar.number_input("Page size", value=5, min_value=0, max_value=10)
        gd = GridOptionsBuilder.from_dataframe(df_selection)
        gd.configure_pagination(enabled=True)
        gd.configure_default_column(editable=True,groupable=True)
        cellstyle_jscode = JsCode("""
            function(params){
                if (params.value == '2021') {
                    return {
                        'color': '#E6E6E6',
                        'backgroundColor' : '#287E8F'
                }
                }
                if (params.value == '2022') {
                    return{
                        'color'  : '#E6E6E6',
                        'backgroundColor' : '#15CAB6'
                    }
                }
                else{
                    return{
                        'color': '#E6E6E6',
                        'backgroundColor': '#EF8A5A'
                    }
                }
        
        };
        """)

        gridOptions = gd.build()
        grid_table = AgGrid(
                df_selection,
                editable=False,
                height=350,
                data_return_mode="filtered_and_sorted",
                gridOptions=gridOptions,
                update_mode= GridUpdateMode.SELECTION_CHANGED,
                fit_columns_on_grid_load=True,
                theme = "streamlit",
                allow_unsafe_jscode=True
                )
    # ---- DATA TABLE ----
    # ---- STREAMLIT RENDER ----

def main():
    # ---- MAIN FUNCTION ----
    setting_path = r"cfg/setting.yaml"
    readme_path = r"README.md"
    cfg = os.path.abspath(setting_path)
    readme = os.path.abspath(readme_path)
    payout_calculator(cfg, readme)
    streamlit_render()
    # ---- MAIN FUNCTION ----

if __name__ == "__main__":
    st.set_page_config(
        page_title="FS-Income Dashboard",
        page_icon="https://i.imgur.com/pyasxls.png",
        layout="wide",
        initial_sidebar_state="auto"
    )
    main ()
