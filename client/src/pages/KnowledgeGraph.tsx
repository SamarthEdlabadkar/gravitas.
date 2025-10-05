import { ArrowLeft } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import DynamicGraph from "@/components/DynamicGraph";
import { Skeleton } from "@/components/ui/skeleton";

// --- Type Definitions ---
type Publication = {
  pmc_id: string;
  title: string;
  authors: string;
  journal: string;
  link: string;
  year: number | string;
  abstract: string;
  categories?: string[];
};

type KGNode = {
    pmc_id: string;
    title: string;
}

const KnowledgeGraph = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // --- Get initial data from location state ---
  const initialPublication: Publication | null = location.state?.publication || null;
  const searchQuery: string | null = location.state?.query || null; // Get the original search query

  // --- State Management for Dynamic Updates ---
  const [currentPublication, setCurrentPublication] = useState<Publication | null>(initialPublication);
  const [summaryData, setSummaryData] = useState<Publication | null>(null);
  const [childNodes, setChildNodes] = useState<KGNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userPath, setUserPath] = useState<Publication[]>(initialPublication ? [initialPublication] : []);

  // --- API Fetching Logic ---
  useEffect(() => {
    if (!currentPublication || !searchQuery) {
      setIsLoading(false);
      setError("No publication data or search query found. Please return to the previous page.");
      return;
    }

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // --- MODIFIED FETCH CALL ---
        // The summary call is now a POST request sending both the query and the current publication's ID.
        const [summaryRes, kgNodeRes] = await Promise.all([
          fetch(`/api/summary`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
              query: searchQuery, 
              pmc_id: currentPublication.pmc_id 
            }),
          }),
          fetch(`/api/kg_node/${currentPublication.pmc_id}`)
        ]);

        if (!summaryRes.ok || !kgNodeRes.ok) {
          throw new Error('Failed to fetch data from the server.');
        }

        const rawSummary = await summaryRes.json();
        const rawKgNodes = await kgNodeRes.json();

        // --- PARSE SUMMARY RESPONSE ---
        if (Array.isArray(rawSummary) && rawSummary.length === 2) {
            const [summaryText, summaryMeta] = rawSummary;
            
            const parseAbstract = (text: string) => {
                if (text.includes('Abstract:')) return text.split('Abstract:')[1]?.trim() || '';
                if (text.includes('Description:')) return text.split('Description:')[1]?.trim() || '';
                return text;
            };

            const formattedSummary: Publication = {
                pmc_id: summaryMeta.pmc_id || currentPublication.pmc_id,
                title: summaryMeta.title,
                authors: summaryMeta.authors,
                journal: summaryMeta.journal || 'N/A',
                link: summaryMeta.link,
                year: summaryMeta.year || 'N/A',
                abstract: parseAbstract(summaryText),
            };
            setSummaryData(formattedSummary);
        } else {
            throw new Error('Unexpected summary API response format');
        }

        // --- PARSE KG_NODE RESPONSE ---
        if (Array.isArray(rawKgNodes)) {
            const formattedChildNodes = rawKgNodes.map(node => {
                const meta = node[1];
                return {
                    pmc_id: meta.pmc_id || meta.osd_id,
                    title: meta.title
                };
            }).filter(node => node.pmc_id && node.title);
            setChildNodes(formattedChildNodes);
        } else {
             throw new Error('Unexpected kg_node API response format');
        }

      } catch (err: any) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [currentPublication, searchQuery]); // Re-run effect when the current publication changes

  // --- Node Click Handler for Interactivity ---
  const handleNodeClick = (nodeId: string) => {
    // Find the full node data from the childNodes state
    const clickedNode = childNodes.find(node => node.pmc_id === nodeId);
    // Prevent re-fetching if the same node is clicked
    if (clickedNode && clickedNode.pmc_id !== currentPublication?.pmc_id) {
        // Create a partial publication object for the new node
        const newPublication: Publication = {
            pmc_id: clickedNode.pmc_id,
            title: clickedNode.title,
            authors: '', journal: '', link: '', year: '', abstract: '' // Blank data to be filled by fetch
        };
        // Set it as the new current publication, which triggers the useEffect
        setCurrentPublication(newPublication);
        // Add the new publication to the user's exploration path
        setUserPath(prevPath => [...prevPath, newPublication]);
    }
  };

  const rootNodeForGraph = currentPublication ? { id: currentPublication.pmc_id, label: currentPublication.title } : null;

  return (
    <div className="min-h-screen w-full p-6">
      {/* Header */}
      <div className="max-w-[1800px] mx-auto mb-6">
        <Button variant="ghost" onClick={() => navigate(-1)} className="gap-2 hover:bg-card/50">
          <ArrowLeft className="h-4 w-4" /> Back to Previous Page
        </Button>
      </div>

      {/* Main Content */}
      <div className="max-w-[1800px] mx-auto grid grid-cols-[15%_55%_30%] gap-6 h-[calc(100vh-140px)]">
        
        {/* Left Column - User Path */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Exploration Path</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
             {userPath.map((p, index) => (
                <Badge key={`${p.pmc_id}-${index}`} variant={index === userPath.length - 1 ? "default" : "secondary"} className="whitespace-normal text-left h-auto">
                    {p.title}
                </Badge>
            ))}
          </CardContent>
        </Card>

        {/* Center Column - Knowledge Graph */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="h-full pt-6">
            {isLoading && <div className="w-full h-full bg-muted/20 rounded-lg flex items-center justify-center"><p>Loading Graph...</p></div>}
            {error && <div className="w-full h-full bg-destructive/20 rounded-lg flex items-center justify-center p-4"><p className="text-destructive-foreground text-center">{error}</p></div>}
            {!isLoading && !error && rootNodeForGraph && (
              <DynamicGraph
                rootNode={rootNodeForGraph}
                childNodes={childNodes.map(node => ({ id: node.pmc_id, label: node.title }))}
                onNodeClick={handleNodeClick} // Updated to use the new handler
              />
            )}
          </CardContent>
        </Card>

        {/* Right Column - Summary Panel */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-2xl font-semibold">Publication Summary</CardTitle>
            <CardDescription>
              Details for: <span className="font-semibold text-primary">{currentPublication?.title || "..."}</span>
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[calc(100%-100px)]">
            <ScrollArea className="h-full pr-4">
              {isLoading && (
                <div className="space-y-4">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-1/2" />
                </div>
              )}
              {error && !isLoading && <p className="text-destructive">Could not load summary for this publication.</p>}
              {!isLoading && !error && summaryData && (
                <div className="space-y-6 text-sm">
                  <div>
                    <h3 className="font-semibold text-base mb-2 text-foreground">Abstract</h3>
                    <p className="text-muted-foreground leading-relaxed">{summaryData.abstract}</p>
                  </div>
                  <div>
                    <h3 className="font-semibold text-base mb-2 text-foreground">Details</h3>
                    <div className="space-y-1 text-muted-foreground">
                      <p><strong>Authors:</strong> {summaryData.authors}</p>
                      <p><strong>Journal:</strong> {summaryData.journal}</p>
                      <p><strong>Year:</strong> {summaryData.year}</p>
                    </div>
                  </div>
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default KnowledgeGraph;