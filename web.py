import logging
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import parse_qs
from processors.database import Database, Config
from processors.experiment import concat_experiments

url_basename = '/traces/'
app = dash.Dash(__name__, url_base_pathname = url_basename)
server = app.server
db = Database(Config('local-config.json'))

channel_dict = {
    '2475ChA ex280/em350': 'Trp',
    '2475ChB ex488/em509': 'GFP'
}

def get_hplc_graphs(exp, view_range = None):
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

        if view_range is not None:
            fig.update_xaxes(autorange = False, range = view_range)

    return raw_graphs

def get_fplc_graphs(exp):
    fplc = exp.fplc

    if fplc is None:
        return None

    
    fplc = fplc.loc[(fplc.Normalization == 'Signal') & (fplc.Channel == 'mAU')]

    samples = set(fplc['Sample'])

    # Using GO primitives b/c plotly express creates traces which are zero
    # outside the defined fraction region, resulting in strange fill behavior
    # when non-continuous fractions are selected.
    
    if len(samples) == 1:
        fplc_graph = go.Figure()
        for frac in set(fplc['Fraction']):
            fplc_graph.add_trace(
                go.Scatter(
                    x = fplc[fplc.Fraction == frac]['mL'],
                    y = fplc[fplc.Fraction == frac]['Value'],
                    mode = 'lines',
                    fill = 'tozeroy',
                    visible = 'legendonly',
                    # if you don't rename them, fraction numbering is off by one
                    name = f'Fraction {frac}'
                )
            )
        fplc_graph.add_trace(
            # want the overall FPLC curve as a separate trace so that it stays present
            # to give overall sense of quality of trace
            go.Scatter(
                x = fplc['mL'],
                y = fplc['Value'],
                mode = 'lines',
                showlegend = False,
                line = {'color': 'black'}
            )
        )
    else:
        fplc_graph = px.line(
            data_frame = fplc,
            x = 'mL',
            y = 'Value',
            color = 'Sample',
            facet_row = 'Normalization',
            template = 'plotly_white'
        )
        try:
            fplc_graph.layout.yaxis2.update(matches = None)
        except AttributeError:
            pass
        # remove 'Channel=' from the facet labels
        fplc_graph.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fplc_graph.update_layout(template = 'plotly_white')
    fplc_graph.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    return fplc_graph

def get_plotly(exp, view_range = None):
    combined_graphs = {}
    html_graphs = []
    
    if exp.hplc is not None:
        combined_graphs['Signal'], combined_graphs['Normalized'] = get_hplc_graphs(exp, view_range)

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

def parse_query(q_string):
    q_string = parse_qs(q_string.replace('?', ''))

    if 'norm-range' in q_string.keys():
        norm_range = q_string['norm-range'][0].split('-')
        norm_range = [float(x) for x in norm_range]
    else:
        norm_range = None

    if 'view-range' in q_string.keys():
        view_range = q_string['view-range'][0].split('-')
        view_range = [float(x) for x in view_range]
    else:
        view_range = None

    return norm_range, view_range

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
                    html.Hr(),
                    html.Button(
                        'Renormalize HPLC',
                        id = 'renorm-hplc',
                        style = {'width': '100%'}
                    ),
                    html.Button(
                        'Reset HPLC',
                        id = 'reset-hplc',
                        style = {'width': '100%'}
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

# Update graph experiment title

@app.callback(
    dash.dependencies.Output('output-container', 'children'),
    [dash.dependencies.Input('root-location', 'pathname')])
def update_output(pathname):
    experiment_name = pathname.replace(url_basename, '').replace('+', ' and ')
    return f'{experiment_name}'

# Make URL pathname the experiment name(s)

@app.callback(
    dash.dependencies.Output('root-location', 'pathname'),
    [dash.dependencies.Input('experiment_dropdown', 'value')]
)
def update_output(value):
    if value is not None:
        return '+'.join(value)

# load graphs, normalize experiment, update query string

@app.callback(
    dash.dependencies.Output('main_graphs', 'children'),
    [
        dash.dependencies.Input('root-location', 'pathname'),
        dash.dependencies.Input('root-location', 'search'),
        dash.dependencies.Input('renorm-hplc', 'n_clicks'),
        dash.dependencies.Input('reset-hplc', 'n_clicks')
    ]
)
def update_output(pathname, search_string, n_clicks, reset):
    changed = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if changed == 'root-location.search' or changed is None:
        raise dash.exceptions.PreventUpdate

    if pathname != '':
        
        path_string = pathname.replace('/traces/', '')
        experiment_name_list = path_string.split('+')
        
        norm_range, view_range = parse_query(search_string)

        if changed == 'renorm-hplc.n_clicks':
            norm_range = view_range

        if len(experiment_name_list) == 1:
            exp = db.pull_experiment(experiment_name_list[0])
        else:
            exp_list = [db.pull_experiment(x) for x in experiment_name_list]
            exp = concat_experiments(exp_list)

        if norm_range is not None:
            exp.renormalize_hplc(norm_range, False)
        
        return get_plotly(exp, view_range)

@app.callback(
    dash.dependencies.Output('root-location', 'search'),
    [
        dash.dependencies.Input('data-Signal', 'relayoutData'),
        dash.dependencies.Input('root-location', 'search'),
        dash.dependencies.Input('renorm-hplc', 'n_clicks'),
        dash.dependencies.Input('reset-hplc', 'n_clicks')
    ]
)
def refresh_xrange(relayout_data, search_string, n_clicks, reset):
    changed = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if relayout_data == None or changed == 'root-location.search':
        raise dash.exceptions.PreventUpdate
        
    if changed == 'reset-hplc.n_clicks':
        return ''
    

    try:
        data = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']]
    except KeyError:
        try:
            if relayout_data['xaxis2.autorange']:
                data = None
        except KeyError:
            raise dash.exceptions.PreventUpdate

    norm_range, view_range = parse_query(search_string)

    new_q_string = '?'

    if changed == 'renorm-hplc.n_clicks':
        new_q_string = new_q_string + f'norm-range={view_range[0]}-{view_range[1]}&'
    elif norm_range is not None:
        new_q_string = new_q_string + f'norm-range={norm_range[0]}-{norm_range[1]}&'

    if data is not None:
        new_q_string = new_q_string + f'view-range={data[0]}-{data[1]}'

    return new_q_string
    

if __name__ == '__main__':
    app.run_server(debug = True, port = '8080')