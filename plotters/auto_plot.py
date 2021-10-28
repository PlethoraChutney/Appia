import plotly.express as px
import plotly.graph_objects as go
import logging
import pandas as pd
import os

def limit_fixer(df_limits, input_limits):
    limits = []
    funs = [max, min]
    for i in [0, 1]:
            if input_limits[i] == 'auto':
                limits.append(df_limits[i])
            else:
                try:
                    input_limits[i] = float(input_limits[i])
                    limits.append(funs[i](df_limits[i], input_limits[i]))
                except ValueError:
                    logging.warning(f'Could not convert "{limits[i]}" to number. Using auto limit.')
                    limits.append(df_limits[i])


    return limits

def auto_plot_hplc(df, limits, xax_var):
    df = df[::10]
    df_lims = [min(df[xax_var]), max(df[xax_var])]
    limits = limit_fixer(df_lims, limits)
    
    fig = px.line(
        df,
        x = xax_var,
        y = 'Value',
        color = 'Sample',
        facet_col = 'Channel',
        facet_row = 'Normalization',
        template = 'plotly_white'
    ).update_yaxes(
        matches = None
    ).update_xaxes(
        range = limits
    )

    return fig


def auto_plot_fplc(df, limits, fractions, xax_var):
    df = df[df['Channel'] == 'mAU']
    df_lims = [min(df[xax_var]), max(df[xax_var])]
    df_fractions = [min(df['Fraction']), max(df['Fraction'])]
    limits = limit_fixer(df_lims, limits)
    frac_lims = [int(x) for x in limit_fixer(df_fractions, fractions[0:2])]

    try:
        assert fractions[2] != 'auto'
        fractions = range(frac_lims[0], frac_lims[1] + 1, int(fractions[2]))
    except (AssertionError, IndexError):
        fractions = range(frac_lims[0], frac_lims[1] + 1)
    except TypeError:
        logging.warning(f'Could not convert "{fractions[2]}" to integer. Plotting all fractions in range.')
        fractions = range(frac_lims[0], frac_lims[1] + 1)

    samples = df['Sample'].unique()

    if len(samples) == 1:
        df = df[df['Normalization'] == 'Signal']
        frac_df = df[(df['Fraction'].isin(fractions))]
        fig = go.Figure()
        for frac in fractions:
            fig.add_trace(
                go.Scatter(
                    x = frac_df[frac_df.Fraction == frac]['mL'],
                    y = frac_df[frac_df.Fraction == frac]['Value'],
                    mode = 'lines',
                    fill = 'tozeroy',
                    # if you don't rename them, fraction numbering is off by one
                    name = f'Fraction {frac}'
                )
            ).update_layout(template = 'plotly_white')
        fig.add_trace(
            # want the overall FPLC curve as a separate trace so that it stays present
            # to give overall sense of quality of trace
            go.Scatter(
                x = df['mL'],
                y = df['Value'],
                mode = 'lines',
                showlegend = False,
                text = df['Fraction'],
                line = {'color': 'black'}
            )
        )
    else:
        fig = px.line(
            data_frame = df,
            x = 'mL',
            y = 'Value',
            color = 'Sample',
            facet_row = 'Normalization',
            hover_data = ['Value', 'mL', 'Fraction'],
            template = 'plotly_white'
        )
        try:
            fig.layout.yaxis2.update(matches = None)
        except AttributeError:
            pass
        # remove 'Channel=' from the facet labels
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

    fig.update_yaxes(
        matches = None
    ).update_xaxes(
        range = limits
    )

    return fig
