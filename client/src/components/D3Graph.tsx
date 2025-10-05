import { useState } from "react";
import HeroBg from "@/assets/hero-bg.jpg";

// --- Type Definitions for nodes ---
type RootNodeType = {
  id: string;
  label: string;
  imageUrl: string;
  x: number;
  y: number;
  isRoot: true;
};

type ChildNodeType = {
  id: string;
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

// The core component for rendering the radial graph
const RadialNetworkGraph = () => {
  // --- Component State & Configuration ---
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Graph dimensions and properties, adjusted for new design
  const width = 700;
  const height = 700;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = 225;
  const nodeRadius = 12; // Made child nodes smaller
  const rootNodeRadius = 70; // Made root node much bigger

  // --- Data Definition ---
  // Define the central root node with an image and surrounding child nodes
  const rootNode = {
    id: 'root',
    label: 'Space Biology',
    // Using a placeholder image as local assets aren't directly usable
    imageUrl: HeroBg,
  };

  const childNodesData: { id: string; label: string }[] = [
    { id: 'node-0', label: 'Governance' },
    { id: 'node-1', label: 'Ethics' },
    { id: 'node-2', label: 'Data Science' },
    { id: 'node-3', label: 'Global Risks' },
    { id: 'node-4', label: 'Misinformation' },
    { id: 'node-5', label: 'Geopolitics' },
    { id: 'node-6', label: 'Workforce' },
    { id: 'node-7', label: 'Foundation Models' },
    { id: 'node-8', label: 'Regulation' },
    { id: 'node-9', label: 'Innovation' },
  ];

  // --- Position Calculation ---
  // Calculate positions for nodes and their labels
  const nodes: NodeType[] = [
    { ...rootNode, x: centerX, y: centerY, isRoot: true },
    ...childNodesData.map((node, index) => {
      const angle = (index / childNodesData.length) * 2 * Math.PI - Math.PI / 2;
      const textRadius = radius + nodeRadius + 20; // Radius for text positioning

      // Determine text anchor based on angle for better readability
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
        textY: centerY + textRadius * Math.sin(angle) + 5, // slight vertical offset
        textAnchor: textAnchor,
        isRoot: false as const,
      };
    }),
  ];

  // --- Rendering ---
  return (
    <div className="bg-background/50 rounded-2xl shadow-2xl overflow-hidden border border-gray-700"
        style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
        }}
    >
      <svg viewBox={`0 0 ${width} ${height}`} width="78%" height="100%">
        {/* Defs for image pattern and filters */}
        <defs>
          <pattern
            id="rootImage"
            height="100%"
            width="100%"
            viewBox={`0 0 ${rootNodeRadius * 2} ${rootNodeRadius * 2}`}
          >
            <image
              href={rootNode.imageUrl}
              x="0"
              y="0"
              height={rootNodeRadius * 2}
              width={rootNodeRadius * 2}
              preserveAspectRatio="xMidYMid slice"
            />
          </pattern>
        </defs>

        {/* Render Edges (Lines) */}
        <g>
          {/* We cast the sliced array to ensure TypeScript knows these are child nodes */}
          {(nodes.slice(1) as ChildNodeType[]).map((node) => {
            // Calculate the end point of the line so it touches the edge of the circle
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
                  stroke:
                    hoveredNode === node.id || hoveredNode === 'root'
                      ? '#FFFFFF'
                      : '#4A4A4A',
                }}
              />
            );
          })}
        </g>

        {/* Render Node Circles */}
        <g>
          {nodes.map((node) => (
            <g
              key={node.id}
              onMouseEnter={() => setHoveredNode(node.id)}
              onMouseLeave={() => setHoveredNode(null)}
            >
              <g>
                {/* Node Circle */}
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.isRoot ? rootNodeRadius : nodeRadius}
                  fill={node.isRoot ? '#0a0a0a' : (hoveredNode === node.id ? '#0a0a0a' : 'none')} // Set root node background to black
                  fillOpacity="0.9"
                  stroke={'#FFFFFF'}
                  strokeWidth={node.isRoot ? 1 : 1.5}
                  className="cursor-pointer transition-all duration-300"
                  style={{
                    transformOrigin: `${node.x}px ${node.y}px`,
                    transform:
                      hoveredNode === node.id ? 'scale(1.2)' : 'scale(1)',
                  }}
                />

                {/* Centered Text for Root Node */}
                {node.isRoot && (
                  <text
                    x={node.x}
                    y={node.y}
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="#FFFFFF"
                    fontSize="16px"
                    fontWeight="bold"
                    className="pointer-events-none"
                  >
                    {node.label}
                  </text>
                )}
              </g>
            </g>
          ))}
        </g>

        {/* Render Text Labels for Child Nodes */}
        <g>
          {(nodes.slice(1) as ChildNodeType[]).map((node) => (
            <text
              key={`text-${node.id}`}
              x={node.textX}
              y={node.textY}
              textAnchor={node.textAnchor}
              fill="#CCCCCC"
              fontSize="14px"
              className="pointer-events-none select-none transition-all duration-300"
              style={{
                fill:
                  hoveredNode === node.id || hoveredNode === 'root'
                    ? '#FFFFFF'
                    : '#CCCCCC',
                fontWeight:
                  hoveredNode === node.id || hoveredNode === 'root'
                    ? 'bold'
                    : 'normal',
              }}
            >
              {node.label}
            </text>
          ))}
        </g>
      </svg>
    </div>
  );
};

export default RadialNetworkGraph;