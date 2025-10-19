import { useState, useRef, useEffect } from "react";
import type { 
  WrappedTextProps, 
  DynamicGraphProps, 
  ChildNodeType, 
  NodeType 
} from "@/types";


// A helper component to handle SVG text wrapping (Keep as is)
const WrappedText = ({ label, x, y, textAnchor, style }: WrappedTextProps) => {
    const MAX_CHARS_PER_LINE = 20;
    const LINE_HEIGHT = 1.1; // ems

    const words = label.split(' ');
    const lines: string[] = [];
    let currentLine = '';

    words.forEach((word: string) => {
        if ((currentLine + word).length > MAX_CHARS_PER_LINE) {
            lines.push(currentLine.trim());
            currentLine = word + ' ';
        } else {
            currentLine += word + ' ';
        }
    });
    lines.push(currentLine.trim());

    // Calculate the initial y-offset to vertically center the text block
    const yOffset = -((lines.length - 1) * LINE_HEIGHT) / 2;

    return (
        <text
            x={x}
            y={y}
            textAnchor={textAnchor}
            dominantBaseline="middle"
            style={style}
            className="pointer-events-none select-none transition-all duration-300"
        >
            {lines.map((line, index) => (
                <tspan key={index} x={x} dy={`${index === 0 ? yOffset : LINE_HEIGHT}em`}>
                    {line}
                </tspan>
            ))}
        </text>
    );
};


// The core component for rendering the radial graph
const DynamicGraph = ({ rootNode, childNodes: childNodesData, onNodeClick }: DynamicGraphProps) => {
  // --- Component State & Configuration ---
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 700, height: 700 });

  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        // Set a minimum size to avoid layout issues
        const size = Math.max(300, Math.min(width, height));
        setDimensions({ width: size, height: size });
      }
    };

    // Initial size set
    handleResize();

    const resizeObserver = new ResizeObserver(handleResize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // **Guard Clause for empty data**
  if (!rootNode || !childNodesData) {
      return (
          <div className="flex items-center justify-center h-full">
              <p className="text-muted-foreground">No graph data available.</p>
          </div>
      );
  }


  const { width, height } = dimensions;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;
  const nodeRadius = 10;
  const rootNodeRadius = Math.max(40, Math.min(width, height) / 8);

  // --- Position Calculation ---
  const nodes: NodeType[] = [
    // Use the prop-passed rootNode
    { ...rootNode, x: centerX, y: centerY, isRoot: true }, 
    
    // Use the prop-passed childNodesData
    ...childNodesData.map((node, index) => {
      const angle = (index / childNodesData.length) * 2 * Math.PI - Math.PI / 2;
      const textRadius = radius + nodeRadius + 25; 

      let textAnchor: 'start' | 'middle' | 'end' = 'middle';
      const cosAngle = Math.cos(angle);
      if (cosAngle > 0.1) textAnchor = 'start';
      if (cosAngle < -0.1) textAnchor = 'end';

      return {
        ...node,
        angle: angle,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
        textX: centerX + textRadius * Math.cos(angle),
        textY: centerY + textRadius * Math.sin(angle),
        textAnchor: textAnchor,
        isRoot: false as const,
      };
    }),
  ];

  // --- Rendering ---
  return (
    <div
      ref={containerRef}
      className="bg-black/50 rounded-2xl shadow-2xl overflow-hidden border border-gray-700"
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        height: '100%',
        minHeight: '300px',
      }}
    >
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%">
        {/* Lines from center to child nodes (keep as is) */}
        <g>
          {(nodes.slice(1) as ChildNodeType[]).map((node) => {
            const endX = centerX + (radius - nodeRadius) * Math.cos(node.angle);
            const endY = centerY + (radius - nodeRadius) * Math.sin(node.angle);
            return (
              <line
                key={`line-${node.id}`}
                x1={centerX}
                y1={centerY}
                x2={endX}
                y2={endY}
                stroke="#4A4A4A"
                strokeWidth="1"
                className="transition-all duration-300"
                style={{
                  stroke: hoveredNode === node.id || hoveredNode === 'root' ? '#FFFFFF' : '#4A4A4A',
                }}
              />
            );
          })}
        </g>

        {/* Node Circles and Root Label (keep as is) */}
        <g>
          {nodes.map((node) => (
            <g
              key={node.id}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
              className="cursor-pointer"
              onClick={() => onNodeClick(node.isRoot ? rootNode.id : node.id)} 
            >
              <g>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.isRoot ? rootNodeRadius : nodeRadius}
                  fill={node.isRoot ? '#0a0a0a' : (hoveredNode === node.id ? '#FFFFFF' : 'none')}
                  stroke={'#FFFFFF'}
                  strokeWidth={node.isRoot ? 1 : 1.5}
                  className="cursor-pointer transition-all duration-300"
                   style={{
                     transformOrigin: `${node.x}px ${node.y}px`,
                     transform: hoveredNode === node.id ? 'scale(1.2)' : 'scale(1)',
                   }}
                />
                {node.isRoot && (
                    <WrappedText
                        label={node.label}
                        x={node.x}
                        y={node.y}
                        textAnchor="middle"
                        style={{
                            fill: '#FFFFFF',
                            fontSize: '12px',
                            fontWeight: 'bold',
                        }}
                    />
                )}
              </g>
            </g>
          ))}
        </g>

        {/* Child Node Labels (keep as is) */}
        <g>
          {(nodes.slice(1) as ChildNodeType[]).map((node) => (
             <WrappedText
                key={`text-${node.id}`}
                label={node.label}
                x={node.textX}
                y={node.textY}
                textAnchor={node.textAnchor}
                style={{
                    fill: hoveredNode === node.id || hoveredNode === 'root' ? '#FFFFFF' : '#CCCCCC',
                    fontWeight: hoveredNode === node.id || hoveredNode === 'root' ? 'bold' : 'normal',
                    fontSize: '14px',
                }}
            />
          ))}
        </g>
      </svg>
    </div>
  );
};

export default DynamicGraph;