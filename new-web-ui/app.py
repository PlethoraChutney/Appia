# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from backend import Experiment, collect_experiments, init_db, update_experiment_list

db = init_db()
experiment_list = update_experiment_list(db)

##### Web app #####

test_experiment = Experiment('test1/')
trace_data = test_experiment.get_plotly()

app = dash.Dash(__name__)

colors = {
    'background': '#FFFFFF',
    'text': '#222222'
}

graphs = []
for channel in trace_data.keys():
    graphs.append(dcc.Graph(
        id=f'channel-{channel}',
        figure={
            'data': trace_data[channel],
            'layout': {
                'title': f'{channel}',
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {'color': colors['text']}
            }
        }
    ))

app.layout = html.Div(
    className = 'container',
    style = {
        'backgroundColor': colors['background']
    },
    children=[
        html.H1(
            children='Baconguis HPLC Reader',
            style = {
                'textAlign': 'center',
                'color': colors['text']
            }
        ),
        html.Div(
            children=f'Simple traces from the comfort of your bench.',
            style = {
                'textAlign': 'center',
                'color': colors['text']
            }
        ),
        html.Div(
            className = 'sidebar',
            children = [
                html.Div(
                    [dcc.Dropdown(
                        id = 'experiment_dropdown',
                        options = [{'label': x, 'value': x} for x in experiment_list]
                    )]
                )
            ]
        ),
        html.Div(
            className = 'graphs',
            children = [
                html.Div(
                    children=[html.H2(children=html.Div(id='output-container'))],
                    style = {
                        'textAlign': 'center',
                        'color': colors['text']
                    }
                ),
                graphs[0],
                graphs[1],
                graphs[2],
                graphs[3]
            ]
        )
    ]
)

@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('experiment_dropdown', 'value')])
def update_output(value):
    return f'Displaying: {value}'

if __name__ == '__main__':
    app.run_server(debug=True)
