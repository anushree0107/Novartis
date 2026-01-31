declare module 'react-plotly.js' {
    import { Component } from 'react';
    import Plotly from 'plotly.js';

    interface PlotParams {
        data: Plotly.Data[];
        layout?: Partial<Plotly.Layout>;
        frames?: Plotly.Frame[];
        config?: Partial<Plotly.Config>;
        style?: React.CSSProperties;
        className?: string;
        useResizeHandler?: boolean;
        onClick?: (event: Plotly.PlotMouseEvent) => void;
        onHover?: (event: Plotly.PlotMouseEvent) => void;
        onUnhover?: (event: Plotly.PlotMouseEvent) => void;
        onSelected?: (event: Plotly.PlotSelectionEvent) => void;
        onRelayout?: (event: Plotly.PlotRelayoutEvent) => void;
        onRestyle?: (event: Plotly.PlotRestyleEvent) => void;
        onRedraw?: () => void;
        onInitialized?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
        onUpdate?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
        onPurge?: (figure: Plotly.Figure, graphDiv: HTMLElement) => void;
        onError?: (err: Error) => void;
        divId?: string;
        revision?: number;
    }

    class Plot extends Component<PlotParams> { }

    export default Plot;
}
