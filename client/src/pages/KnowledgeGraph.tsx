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
  year: number | string; // Year can be a string from the API
  abstract: string;
  categories?: string[]; // Make categories optional
};

// Represents a related publication for child nodes
type KGNode = {
    pmc_id: string;
    title: string;
}

const KnowledgeGraph = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const publication: Publication | null = location.state?.publication || null;

  // --- State for fetched data ---
  const [summaryData, setSummaryData] = useState<Publication | null>(null);
  const [childNodes, setChildNodes] = useState<KGNode[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [userPath, setUserPath] = useState<Publication[]>([]);

  // --- API Fetching Logic ---
  useEffect(() => {
    if (!publication) {
      setIsLoading(false);
      setError("No publication data found. Please return to the previous page and select a publication.");
      return;
    }

    setUserPath([publication]);

    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [summaryRes, kgNodeRes] = await Promise.all([
          fetch(`/api/summary?pmc_id=${publication.pmc_id}`),
          fetch(`/api/kg_node/${publication.pmc_id}`)
        ]);

        if (!summaryRes.ok || !kgNodeRes.ok) {
          throw new Error('Failed to fetch data from the server.');
        }

        const rawSummary = await summaryRes.json();
        const rawKgNodes = await kgNodeRes.json();

        // --- PARSE SUMMARY RESPONSE ---
        if (Array.isArray(rawSummary) && rawSummary.length === 2) {
            const [summaryText, summaryMeta] = rawSummary;
            
            // Helper to extract abstract from the combined string
            const parseAbstract = (text: string) => {
                if (text.includes('Abstract:')) return text.split('Abstract:')[1]?.trim() || '';
                if (text.includes('Description:')) return text.split('Description:')[1]?.trim() || '';
                return text;
            };

            const formattedSummary: Publication = {
                pmc_id: summaryMeta.pmc_id || publication.pmc_id,
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
                const meta = node[1]; // The metadata object is the second element
                return {
                    pmc_id: meta.pmc_id || meta.osd_id,
                    title: meta.title
                };
            }).filter(node => node.pmc_id && node.title); // Filter out any malformed nodes
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
  }, [publication]);

  const rootNodeForGraph = publication ? { id: publication.pmc_id, label: publication.title } : null;

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
          <CardContent>
             {userPath.map(p => <Badge key={p.pmc_id} className="whitespace-normal text-left">{p.title}</Badge>)}
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
                onNodeClick={(label) => console.log(label)} // Placeholder for node click
              />
            )}
          </CardContent>
        </Card>

        {/* Right Column - Summary Panel */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-2xl font-semibold">Publication Summary</CardTitle>
            <CardDescription>
              Details for: <span className="font-semibold text-primary">{publication?.title || "..."}</span>
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
              {error && <p className="text-destructive">{error}</p>}
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