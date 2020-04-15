import React, { useRef, FunctionComponent, useEffect } from 'react';
import dagreD3 from 'dagre-d3';
import * as d3 from 'd3';

type DagProps = {
    data: any;
    height: number;
    width: number;
}

const Dag: FunctionComponent<DagProps> = ({width, height, data}) => {
  const container = useRef(null);
  const dag = useRef(null);
  const render = dagreD3.render();

  useEffect(() => {
    if(!data || !container.current || !dag.current) return
    const inner = d3.select(dag.current);
    const svg = d3.select(container.current);

    // set up zoom
    const zoom = d3.zoom().on("zoom", function() {
      inner.attr("transform", d3.event.transform);
    });
    svg.call(zoom);
    
    // init graph
    const graph = new dagreD3.graphlib.Graph()
    .setGraph({
      rankdir: "LR",
    })
    .setDefaultEdgeLabel(function() {return {}});

    // add data to graph
    data.forEach((d) => {
      graph.setNode(d.id, {
        label: d.id,
        rx: 5,
        ry: 5,
      })
      d.parentIds.forEach((parent) => {
        graph.setEdge(parent, d.id)
      })
    })

    // render
    render(inner, graph);

    //set up zoom transformation based on graph
    const initialScale = 3;
    svg.call(zoom.transform, d3.zoomIdentity.translate((parseInt(svg.attr("width")) - graph.graph().width * initialScale) / 2, 20).scale(initialScale));

    //TODO fit graph to screen and center
  }, [data, container, dag])


  return (<svg
    width={width}
    height={height}
    ref={container}
    className="dag-container"
    >
      <g className="dag" ref={dag}></g>
      </svg>
  )
};

export default Dag;
