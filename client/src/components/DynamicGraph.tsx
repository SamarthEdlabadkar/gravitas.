import React, { useState, useRef, useEffect } from "react";

// --- Type Definitions for nodes ---
type RootNodeType = {
  id: string;
  label: string;
  x: number;
  y: number;
  isRoot: true;
};

type ChildNodeType = {
  id:string;
  label: string;
  angle: number;
  x: number;
  y: number;
  textX: number;
  textY: number;
  textAnchor: 'start' | 'middle' | 'end';
  isRoot: false;
};

type NodeType = RootNodeType | ChildNodeType;

// --- Prop Types for the component ---
interface DynamicGraphProps {
    rootNode: { id: string; label: string };
    childNodes: { id: string; label: string }[];
    onNodeClick: (label: string | null) => void;
}

// Helper component for SVG text wrapping (no changes needed here)
const WrappedText = ({ label, x, y, textAnchor, style }) => {
    const MAX_CHARS_PER_LINE = 20;
    const LINE_HEIGHT = 1.1; // ems
    const words = label.split(' ');
    const lines: string[] = [];
    let currentLine = '';
    words.forEach(word => {
        if ((currentLine + word).length > MAX_CHARS_PER_LINE) {
            lines.push(currentLine.trim());
            currentLine = word + ' ';
        } else {
            currentLine += word + ' ';
        }
    });
    lines.push(currentLine.trim());
    const yOffset = -((lines.length - 1) * LINE_HEIGHT) / 2;
    return (
        <text x={x} y={y} textAnchor={textAnchor} dominantBaseline="middle" style={style} className="pointer-events-none select-none transition-all duration-300">
            {lines.map((line, index) => (
                <tspan key={index} x={x} dy={`${index === 0 ? yOffset : LINE_HEIGHT}em`}>{line}</tspan>
            ))}
        </text>
    );
};

// The core component for rendering the radial graph
const DynamicGraph: React.FC<DynamicGraphProps> = ({ rootNode, childNodes: childNodesData, onNodeClick }) => {
  // --- Component State & Configuration ---
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 700, height: 700 });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        const size = Math.max(300, Math.min(width, height));
        setDimensions({ width: size, height: size });
      }
    };
    handleResize();
    const resizeObserver = new ResizeObserver(handleResize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }
    return () => resizeObserver.disconnect();
  }, []);

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

  // --- Position Calculation using props ---
  const nodes: NodeType[] = [
    { ...rootNode, x: centerX, y: centerY, isRoot: true },
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
    <div ref={containerRef} className="bg-background/30 rounded-lg overflow-hidden border border-border/50" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', width: '100%', height: '100%', minHeight: '300px' }}>
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%">
        {/* Lines from center to child nodes */}
        <g>
          {(nodes.slice(1) as ChildNodeType[]).map((node) => {
            const endX = centerX + (radius - nodeRadius) * Math.cos(node.angle);
            const endY = centerY + (radius - nodeRadius) * Math.sin(node.angle);
            return (
              <line
                key={`line-${node.id}`} x1={centerX} y1={centerY} x2={endX} y2={endY}
                stroke="hsl(var(--border))" strokeWidth="1" className="transition-all duration-300"
                style={{ stroke: hoveredNode === node.id || hoveredNode === 'root' ? 'hsl(var(--primary))' : 'hsl(var(--border))' }}
              />
            );
          })}
        </g>
        
        {/* Node Circles and Root Label */}
        <g>
          {nodes.map((node) => (
            <g key={node.id} onMouseEnter={() => setHoveredNode(node.id)} onMouseLeave={() => setHoveredNode(null)} className="cursor-pointer" onClick={() => onNodeClick(node.isRoot? null : node.label)}>
                <circle
                    cx={node.x} cy={node.y} r={node.isRoot ? rootNodeRadius : nodeRadius}
                    fill={node.isRoot ? 'hsl(var(--background))' : (hoveredNode === node.id ? 'hsl(var(--primary))' : 'hsl(var(--secondary))')}
                    stroke={'hsl(var(--border))'} strokeWidth={1.5} className="transition-all duration-300"
                    style={{ transformOrigin: `${node.x}px ${node.y}px`, transform: hoveredNode === node.id ? 'scale(1.2)' : 'scale(1)' }}
                />
                {node.isRoot && (
                    <WrappedText
                        label={node.label} x={node.x} y={node.y}
                        textAnchor="middle" style={{ fill: 'hsl(var(--primary-foreground))', fontSize: '12px', fontWeight: 'bold' }}
                    />
                )}
            </g>
          ))}
        </g>

        {/* Child Node Labels */}
        <g>
          {(nodes.slice(1) as ChildNodeType[]).map((node) => (
             <WrappedText
                key={`text-${node.id}`} label={node.label} x={node.textX} y={node.textY}
                textAnchor={node.textAnchor}
                style={{
                    fill: hoveredNode === node.id || hoveredNode === 'root' ? 'hsl(var(--primary-foreground))' : 'hsl(var(--muted-foreground))',
                    fontWeight: hoveredNode === node.id || hoveredNode === 'root' ? 'bold' : 'normal',
                    fontSize: '12px',
                }}
            />
          ))}
        </g>
      </svg>
    </div>
  );
};

export default DynamicGraph;