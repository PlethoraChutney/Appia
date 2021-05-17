import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
from database import Database, Config

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

    fig = px.line(
        data_frame = exp.hplc,
        x = 'mL',
        y = 'Value',
        color = 'Sample',
        facet_row = 'Channel',
        facet_col = 'Normalization',
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

    return fig


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

if __name__ == '__main__':
    app.run_server(debug = True, port = '8080')