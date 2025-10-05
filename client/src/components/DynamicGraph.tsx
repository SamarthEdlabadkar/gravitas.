import { useState, useRef, useEffect } from "react";
import HeroBg from "@/assets/hero-bg.jpg";

// --- Type Definitions for API Data ---

/**
 * The expected structure of a single research paper object from the REST API.
 */
type PaperData = {
  title: string;
  abstract: string;
  authors: string;
  year: number;
  pmc_id: string; // The paper's unique identifier
};

/**
 * The structure of a child node before layout calculation.
 * We use the paper's title as the label.
 */
type RawChildNode = {
  id: string; // Using pmc_id as the unique ID
  label: string; // Paper title
  data: PaperData; // Hold the full paper data
};

// --- Type Definitions for Nodes with Layout (Kept similar) ---
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
  data: PaperData; // Include the paper data in the final node
};

type NodeType = RootNodeType | ChildNodeType;

// --- SIMULATED API CALL ---
const fetchPapers = (): Promise<PaperData[]> => {
  // Replace this with your actual 'fetch' or 'axios' call to your REST endpoint.
  return new Promise((resolve) => {
    setTimeout(() => {
      const apiData: PaperData[] = [
        {title: 'Central', abstract: 'A study on astronaut health.', authors: 'Smith, J.', year: 2020, pmc_id: 'PMC7001' },
        { title: 'The effects of microgravity on human bone density', abstract: 'A study on astronaut health.', authors: 'Smith, J.', year: 2020, pmc_id: 'PMC7001' },
        { title: 'Radiation shielding materials for long-duration space missions', abstract: 'Testing new polymers.', authors: 'Chen, L.', year: 2022, pmc_id: 'PMC7002' },
        { title: 'Plant growth regulation in lunar regolith simulators', abstract: 'Farming in space.', authors: 'Garcia, R.', year: 2023, pmc_id: 'PMC7003' },
        { title: 'Cognitive performance under extreme isolation: a Mars analog study', abstract: 'Psychological factors in deep space.', authors: 'Kowalski, P.', year: 2021, pmc_id: 'PMC7004' },
        { title: 'Transcriptomic analysis of microbial communities in the ISS', abstract: 'Understanding the space microbiome.', authors: 'Davies, A.', year: 2019, pmc_id: 'PMC7005' },
        { title: 'Developing closed-loop life support systems for orbital habitats', abstract: 'Recycling air and water efficiently.', authors: 'Nguyen, T.', year: 2024, pmc_id: 'PMC7006' },
        { title: 'Immunological changes in astronauts post-flight recovery', abstract: 'How the body adapts to Earth.', authors: 'Zheng, X.', year: 2020, pmc_id: 'PMC7007' },
        { title: 'Bio-manufacturing pharmaceuticals in a low-Earth orbit environment', abstract: 'Gravity-free drug production.', authors: 'Miller, S.', year: 2023, pmc_id: 'PMC7008' },
        { title: 'A review of rodent models in space flight research from 2000-2024', abstract: 'Animal studies overview.', authors: 'Almeida, V.', year: 2024, pmc_id: 'PMC7009' },
        { title: 'AI-driven mission control for autonomous biological experiments', abstract: 'Automation in space labs.', authors: 'Jansen, B.', year: 2022, pmc_id: 'PMC7010' },
      ];
      resolve(apiData);
    }, 1000); // Simulate network latency
  });
};

// The core component for rendering the radial graph
const DynamicNetworkGraph = () => {
  // --- Component State & Configuration ---
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 700, height: 700 });
  const [paperNodesData, setPaperNodesData] = useState<RawChildNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const containerRef = useRef<HTMLDivElement>(null);

  // --- Effect Hook for API Data Fetching ---
  useEffect(() => {
    setIsLoading(true);
    fetchPapers()
      .then((data: PaperData[]) => {
        // Map the raw paper data into the structure needed for node processing
        const nodes = data.map(paper => ({
          id: paper.pmc_id,
          label: paper.title, // Use the title as the node label
          data: paper,
        }));
        setPaperNodesData(nodes);
      })
      .catch((error) => {
        console.error("Failed to fetch paper data:", error);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  // --- Effect Hook for Dynamic Resizing (Kept as is) ---
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    const resizeObserver = new ResizeObserver(handleResize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  // --- Layout Calculations ---
  const { width, height } = dimensions;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 3;
  const nodeRadius = 12;
  const rootNodeRadius = 70;
  
  // Define the central root node - its label is the central theme
  const rootNode: Omit<RootNodeType, 'x' | 'y'> = {
    id: 'root',
    label: 'Space Biology Research', // Updated to a central theme
    imageUrl: HeroBg,
    isRoot: true,
  };

  // --- Position Calculation ---
  const processedChildNodes: ChildNodeType[] = paperNodesData.map((node, index) => {
    const angle = (index / paperNodesData.length) * 2 * Math.PI - Math.PI / 2;
    const textRadius = radius + nodeRadius + 20;

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
      textY: centerY + textRadius * Math.sin(angle) + 5,
      textAnchor: textAnchor,
      isRoot: false as const,
    };
  });

  const nodes: NodeType[] = [
    { ...rootNode, x: centerX, y: centerY },
    ...processedChildNodes,
  ];

  // --- Rendering ---

  if (isLoading) {
    return (
      <div
        className="bg-background/50 rounded-2xl shadow-2xl overflow-hidden border border-gray-700"
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          width: '100%',
          height: '100%',
          minHeight: '400px',
          color: '#FFFFFF'
        }}
      >
        Fetching Your Data...
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="bg-background/50 rounded-2xl shadow-2xl overflow-hidden border border-gray-700"
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        width: '100%',
        height: '100%',
      }}
    >
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height="100%">
        {/* Defs for image pattern */}
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
          {processedChildNodes.map((node) => {
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
                  fill={node.isRoot ? 'url(#rootImage)' : (hoveredNode === node.id ? '#FFFFFF' : '#1A1A1A')}
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

                {/* Root Node Label */}
                 {node.isRoot && (
                    <text
                      x={node.x}
                      y={node.y + rootNodeRadius + 20}
                      textAnchor="middle"
                      fill="#FFFFFF"
                      fontSize="18px"
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

        {/* Render Text Labels for Child Nodes (Paper Titles) */}
        <g>
          {processedChildNodes.map((node) => (
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
              {/* Truncate long titles for display (optional, but recommended) */}
              {node.label.length > 30 ? node.label.substring(0, 30) + '...' : node.label}
            </text>
          ))}
        </g>
      </svg>
    </div>
  );
};

export default DynamicNetworkGraph;