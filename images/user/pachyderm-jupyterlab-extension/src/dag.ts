import { Widget } from '@lumino/widgets';
import * as d3 from 'd3';
import * as d3Dag from 'd3-dag';
import { requestAPI } from './api';

const nodeRadius = 20;

const dagProcessor = d3Dag.dagStratify();

const renderGraph = (svgNode, width, height, data) => {
  console.log(data);

  const viewbox = [-nodeRadius, -nodeRadius, width + 2 * nodeRadius, height + 2 * nodeRadius];
  svgNode.attr("viewbox", viewbox.join(" "));

  const dag = dagProcessor(data);

  const defs = svgNode.append('defs'); // For gradients
  
  const layout = d3Dag.sugiyama()
    .size([width, height])
    .layering(d3Dag.layeringLongestPath())
    .decross(d3Dag.decrossOpt())
    .coord(d3Dag.coordCenter());
  layout(dag);
  
  const steps = dag.size();
  const interp = d3.interpolateRainbow;
  const colorMap: object = {};
  dag.each((node: any, i: number) => {
    colorMap[node.id] = interp(i / steps);
  });
  
  // How to draw edges
  const line = d3.line()
    .curve(d3.curveCatmullRom)
    .x(d => d.x)
    .y(d => d.y);
    
  // Plot edges
  svgNode.append('g')
    .selectAll('path')
    .data(dag.links())
    .enter()
    .append('path')
    .attr('d', ({ data }) => line(data.points))
    .attr('fill', 'none')
    .attr('stroke-width', 3)
    .attr('stroke', ({source, target}) => {
      const gradId = `${source.id}-${target.id}`;
      const grad = defs.append('linearGradient')
        .attr('id', gradId)
        .attr('gradientUnits', 'userSpaceOnUse')
        .attr('x1', source.x)
        .attr('x2', target.x)
        .attr('y1', source.y)
        .attr('y2', target.y);
      grad.append('stop').attr('offset', '0%').attr('stop-color', colorMap[source.id]);
      grad.append('stop').attr('offset', '100%').attr('stop-color', colorMap[target.id]);
      return `url(#${gradId})`;
    });
  
  // Select nodes
  const nodes = svgNode.append('g')
    .selectAll('g')
    .data(dag.descendants())
    .enter()
    .append('g')
    .attr('transform', ({x, y}) => `translate(${x}, ${y})`);
  
  // Plot node circles
  nodes.append('circle')
    .attr('r', nodeRadius)
    .attr('fill', n => colorMap[n.id]);
  
  const arrow = d3.symbol().type(d3.symbolTriangle).size(nodeRadius * nodeRadius / 5.0);
  svgNode.append('g')
    .selectAll('path')
    .data(dag.links())
    .enter()
    .append('path')
    .attr('d', arrow)
    .attr('transform', ({ source, target, data }) => {
      const [end, start] = data.points.reverse();
      // This sets the arrows the node radius (20) + a little bit (3) away
      // from the node center, on the last line segment of the edge. This
      // means that edges that only span ine level will work perfectly, but if
      // the edge bends, this will be a little off.
      const dx = start.x - end.x;
      const dy = start.y - end.y;
      const scale = nodeRadius * 1.15 / Math.sqrt(dx * dx + dy * dy);
      // This is the angle of the last line segment
      const angle = Math.atan2(-dy, -dx) * 180 / Math.PI + 90;
      return `translate(${end.x + dx * scale}, ${end.y + dy * scale}) rotate(${angle})`;
    })
    .attr('fill', ({ target }) => colorMap[target.id])
    .attr('stroke', 'white')
    .attr('stroke-width', 1.5);

  // Add text to nodes
  nodes.append('text')
    .text(d => d.id)
    .attr('font-weight', 'bold')
    .attr('font-family', 'sans-serif')
    .attr('text-anchor', 'middle')
    .attr('alignment-baseline', 'middle')
    .attr('fill', 'white');
}

export class DAGWidget extends Widget {
  constructor() {
    super();
    this.id = 'pachyderm-dag-widget';
    this.title.label = 'Pachyderm DAG';
    this.title.closable = true;

    const svgNode = d3.select(this.node)
      .append("svg")
      .attr("width", "100%")
      .attr("height", "100%");

     // TODO: maybe we should use a MutationObserver here to handle resizes
    requestAPI<any>('dag')
      .then(data => {
        const rect = this.node.getBoundingClientRect();
        renderGraph(svgNode, rect.width, rect.height, data);
      })
      .catch(reason => {
        console.error(
          `The pachyderm-jupyterlab-extension server extension appears to be missing.\n${reason}`
        );
      });
  }
}
