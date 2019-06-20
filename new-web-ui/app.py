# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from backend import Experiment, collect_experiments, init_db


##### Web app #####

db = init_db()

trace_exp = Experiment(db['test1'])
trace_df = trace_exp.as_pandas_df()
trace_data = trace_exp.get_plotly()

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#EEEEEE',
    'text': '#000000'
}

graphs = []
i = 1
for graph in trace_data:
    graphs.append(dcc.Graph(
        id=f'example-graph-{i}',
        figure={
            # 'data': [
            #     {'x': trace_df['Time'], 'y': trace_df['Signal'], 'name': trace_df['Sample'], 'type': 'scatter'},
            # ],
            'data': graph,
            'layout': {
                'title': graph['Channel'],
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {'color': colors['text']}
            }
        }
    ))
    i += 1

app.layout = html.Div(
    style = {
        'backgroundColor': colors['background']
    },
    children=[
        html.H1(
            children='Hello Dash',
            style = {
                'textAlign': 'center',
                'color': colors['text']
            }
        ),

        html.Div(
            children='Dash: A web application framework for Python.',
            style = {
                'textAlign': 'center',
                'color': colors['text']
            }
        ),
        graphs[0],
        graphs[1]
        # for graph in trace_data:
        #     dcc.Graph(
        #         id='example-graph-2',
        #         figure={
        #             # 'data': [
        #             #     {'x': trace_df['Time'], 'y': trace_df['Signal'], 'name': trace_df['Sample'], 'type': 'scatter'},
        #             # ],
        #             'data': graph,
        #             'layout': {
        #                 'title': 'Dash Data Visualization',
        #                 'plot_bgcolor': colors['background'],
        #                 'paper_bgcolor': colors['background'],
        #                 'font': {'color': colors['text']}
        #             }
        #         }
        #     )
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)
