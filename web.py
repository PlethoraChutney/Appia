import logging
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from new_commands.database import Database, Config
from new_commands.experiment import concat_experiments

app = dash.Dash(__name__, url_base_pathname = '/traces/')
server = app.server
db = Database(Config('subcommands/local_config.json'))

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

channel_dict = {
    '2475ChA ex280/em350': 'Trp',
    '2475ChB ex488/em509': 'GFP'
}

def get_hplc_graphs(exp):
    exp.rename_channels(channel_dict)
    raw_graphs = []

    for norm in ['Signal', 'Normalized']:

        fig = px.line(
            data_frame = exp.hplc.loc[exp.hplc['Normalization'] == norm],
            x = 'mL',
            y = 'Value',
            color = 'Sample',
            facet_row = 'Channel',
            template = 'plotly_white'
        )

        try:
            # without this, your channels are stuck using the same yaxis range
            fig.layout.yaxis2.update(matches = None)
        except AttributeError:
            # if the trace only has one channel, it doesn't have yaxis2
            pass

        # remove 'Channel=' from the facet labels
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

        raw_graphs.append(fig)

    return raw_graphs

def get_fplc_graphs(exp):
    return None

def get_plotly(exp):
    combined_graphs = {}
    html_graphs = []
    
    if exp.hplc is not None:
        combined_graphs['Signal'], combined_graphs['Normalized'] = get_hplc_graphs(exp)

    if exp.fplc is not None:
        combined_graphs['FPLC'] = get_fplc_graphs(exp)

    for data_type in combined_graphs.keys():
        html_graphs.extend([
                html.H5(
                    children = data_type,
                    style = {'textAlign': 'center'}
                ),
                dcc.Graph(
                    style={'height': 600},
                    id=f'data-{data_type}',
                    figure=combined_graphs[data_type]
                )
            ])

    return html_graphs

def serve_layout():
    return html.Div(
        className = 'container',
        children=[
            dcc.Location(id='root-location', refresh=False),
            html.Div(
                className = 'graph-title',
                children = [
                html.H1(
                    children='Baconguis Chromatography Reader',
                    style = {'textAlign': 'center'}
                ),
                html.Div(
                    children='Simple traces from the comfort of your bench.',
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
                            options = [{'label': x, 'value': x} for x in db.update_experiment_list()],
                            multi = True
                        )]
                    ),
                    html.Button(
                        'Renormalize HPLC',
                        id = 'renom-hplc',
                        style = {'width': '100%', 'padding-left': 'auto'}
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
    experiment_name = hash.replace('#', '').replace('+', ' and ')
    return f'{experiment_name}'

# Make URL hash the experiment name(s)

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
    if hash != '':
        hash_string = hash.replace('#', '')
        experiment_name_list = hash_string.split('+')
        logging.debug(experiment_name_list)

        if len(experiment_name_list) == 1:
            exp = db.pull_experiment(experiment_name_list[0])
        else:
            exp = concat_experiments(experiment_name_list)

        return get_plotly(exp)

if __name__ == '__main__':
    app.run_server(debug = False, port = '8080')