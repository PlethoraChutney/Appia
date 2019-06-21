# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from backend import Experiment, collect_experiments, init_db, update_experiment_list

db = init_db()

##### Web app #####

app = dash.Dash(__name__)

app.layout = html.Div(
    className = 'container',
    children=[
        html.Div(
            className = 'graph-title',
            children = [
            html.H1(
                children='Baconguis HPLC Reader',
                style = {'textAlign': 'center'}
            ),
            html.Div(
                children=f'Simple traces from the comfort of your bench.',
                style = {'textAlign': 'center'}
            ),
            html.Div(
                children=[html.H4(children=html.Div(id='output-container'))],
                style = {'textAlign': 'center'}
            )
            ]
        ),
        html.Div(
            className = 'sidebar',
            children = [
                html.H5(
                    style = {'paddingTop': '10px', 'textAlign': 'center'},
                    children = 'Pick experiment:'
                ),
                html.Div(
                    style = {'padding-top': '10px', 'padding-bottom': '10px'},
                    children =
                    [dcc.Dropdown(
                        id = 'experiment_dropdown',
                        options = [{'label': x, 'value': x} for x in update_experiment_list(db)]
                    )]
                )
            ]
        ),
        html.Div(
            className = 'graphs',
            children = html.Div(id = 'main_graphs')
        )
    ]
)

@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('experiment_dropdown', 'value')])
def update_output(value):
    return f'Displaying: {value}'

@app.callback(
    dash.dependencies.Output('main_graphs', 'children'),
    [dash.dependencies.Input('experiment_dropdown', 'value')]
)
def update_output(value):
    return Experiment(db.get(value)).get_plotly()

if __name__ == '__main__':
    app.run_server(debug=True)
