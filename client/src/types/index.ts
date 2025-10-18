// Type definitions for the medical research search application

export interface PublicationMetadata {
  pmc_id: string;
  title: string;
  authors: string;
  year: number;
  journal: string;
  link: string;
}

export interface Publication {
  pmc_id: string;
  title: string;
  authors: string;
  journal: string;
  link: string;
  year: number | string;
  abstract: string;
  categories: string[];
}

// Raw API response structure
export type APIResponseItem = [
  string, // Abstract text with "Abstract: " prefix
  PublicationMetadata, // Metadata object
  string[] // Categories array
];

export type APIResponse = APIResponseItem[];

// Navigation state types
export interface NetworkPageState {
  results: Publication[];
  query: string;
}

export interface KnowledgeGraphPageState {
  publication: Publication;
  query: string;
}

// Knowledge Graph specific types
export interface KGNode {
  pmc_id: string;
  title: string;
}

export interface GraphNode {
  id: string;
  label: string;
}

// API Response types for Knowledge Graph
export interface SummaryResponse {
  summary: string;
}

export interface KGNodeMetadata {
  pmc_id?: string;
  osd_id?: string;
  title: string;
}

export type KGNodeAPIResponse = [string, KGNodeMetadata][];

export interface KGNodeResponse {
  data: KGNodeAPIResponse;
}

// Graph component types
export interface WrappedTextProps {
  label: string;
  x: number;
  y: number;
  textAnchor: 'start' | 'middle' | 'end';
  style: React.CSSProperties;
}

export interface RadialNetworkGraphProps {
  onNodeClick: (category: string | null) => void;
}

export interface DynamicGraphProps {
  rootNode: { id: string; label: string };
  childNodes: { id: string; label: string }[];
  onNodeClick: (nodeId: string) => void;
}

// Internal node types for graph components
export interface RootNodeType {
  id: string;
  label: string;
  imageUrl?: string;
  x: number;
  y: number;
  isRoot: true;
}

export interface ChildNodeType {
  id: string;
  label: string;
  angle: number;
  x: number;
  y: number;
  textX: number;
  textY: number;
  textAnchor: 'start' | 'middle' | 'end';
  isRoot: false;
}

export type NodeType = RootNodeType | ChildNodeType;

// Error handling
export interface SearchError {
  message: string;
}