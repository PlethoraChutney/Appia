# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
import urllib
from backend import Experiment, collect_experiments, init_db, update_experiment_list
from config import config

db = init_db(config)

##### Web app #####

# I'm serving this app on an nginx server, and I want it to be accessible
# at a non-root URL. You can change this, and remember when you're testing
# changes that you'll have to go to localhost:8050/traces or whatever

app = dash.Dash(__name__, url_base_pathname = '/traces/')
server = app.server

# This string leaves everything up to the plotly default except changes the
# window title.

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Troll - Traces</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
# we make the layout a function that gets run so that you can refresh the page
# to refresh the dropdown options (i.e., find new experiments). If you directly
# build the layout you need to restart the server every time there's a new
# experiment.

def serve_layout():
    return html.Div(
        className = 'container',
        children=[
            dcc.Location(id='root-location', refresh=False),
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
                            options = [{'label': x, 'value': x} for x in update_experiment_list(db)],
                            multi = True
                        ),
                        html.Hr(),
                        html.A(html.Button('Download data', id = 'download-button'), href='', id='download-link', download='rawdata.csv', target='_blank')]
                    )
                ]
            ),
            html.Div(
                className = 'graphs',
                children = html.Div(id = 'main_graphs')
            )
        ]
    )

app.layout = serve_layout

@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('root-location', 'hash')])
def update_output(hash):
    experiment_name = hash.replace('#', '')
    return f'Displaying: {experiment_name}'

@app.callback(
    dash.dependencies.Output('root-location', 'hash'),
    [dash.dependencies.Input('experiment_dropdown', 'value')]
)
def update_output(value):
    if value is not None:
        return '#' + '+'.join(value)

@app.callback(
    dash.dependencies.Output('main_graphs', 'children'),
    [dash.dependencies.Input('root-location', 'hash')]
)
def update_output(hash):
    if hash is not None:
        hash_string = hash.replace('#', '')
        experiment_name_list = hash_string.split('+')
        
        if len(experiment_name_list) == 1:
            return Experiment(db.get(experiment_name_list[0])).get_plotly()

        experiment_list = [Experiment(db.get(x)) for x in experiment_name_list]
        return Experiment(experiment_list).get_plotly()

@app.callback(
    dash.dependencies.Output('download-link', 'href'),
    [dash.dependencies.Input('root-location', 'hash')]
)
def update_download_link(hash):
    df = Experiment(db.get(hash.replace('#', ''))).as_pandas_df()
    csv_string = df.to_csv(index=False, encoding = 'utf-8')
    csv_string = "data:text/csv;charset=utf-8," + urllib.parse.quote(csv_string)
    return csv_string

if __name__ == '__main__':
    app.run_server(debug=True)
