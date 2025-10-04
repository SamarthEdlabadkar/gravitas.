import { ArrowLeft, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNavigate } from "react-router-dom";

const KnowledgeGraph = () => {
  const navigate = useNavigate();

  // Placeholder data for the currently selected node on the graph
  const selectedNode = {
    title: "Human Body",
    description: "This node represents the biological and physiological systems of the human body. In the context of spaceflight, it is the primary subject of study for aerospace medicine, focusing on adaptations and health risks associated with microgravity and cosmic radiation.",
    relationships: [
      "Affected by Spaceflight",
      "Studied in Aerospace Medicine",
      "Impacts Astronaut Health"
    ],
    relatedConcepts: [
      "Microgravity",
      "Cosmic Radiation",
      "Bone Density Loss",
      "Muscle Atrophy",
      "Cardiovascular System",
      "Vestibular System"
    ]
  };

  return (
    <div className="min-h-screen w-full p-6">
      {/* Header with Back Button */}
      <div className="max-w-[1800px] mx-auto mb-6">
        <Button 
          variant="ghost" 
          onClick={() => navigate("/network")}
          className="gap-2 hover:bg-card/50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Network Page
        </Button>
      </div>

      {/* Main Content - Three Column Layout */}
      <div className="max-w-[1800px] mx-auto grid grid-cols-[15%_55%_30%] gap-6 h-[calc(100vh-140px)]">
        
        {/* Left Column - User Path (15%) */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">User Path</CardTitle>
            <CardDescription className="text-xs">Your exploration journey</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-start gap-2">
              <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80 transition-colors">
                Start
              </Badge>
              <ChevronRight className="w-4 h-4 text-muted-foreground rotate-90" />
              <Badge variant="secondary" className="cursor-pointer hover:bg-secondary/80 transition-colors">
                Spaceflight
              </Badge>
              <ChevronRight className="w-4 h-4 text-muted-foreground rotate-90" />
              <Badge variant="outline" className="border-primary/80 bg-primary/10 text-primary cursor-default">
                Human Body
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Center Column - Knowledge Graph Visualization (55%) */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardContent className="h-full pt-6">
            <div className="w-full h-full bg-muted/20 rounded-lg border border-border/50 flex items-center justify-center">
              <div className="text-center space-y-2">
                <div className="w-24 h-24 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary/40" />
                  </div>
                </div>
                <p className="text-muted-foreground text-lg">Knowledge Graph Visualization</p>
                <p className="text-muted-foreground/60 text-sm">Interactive graph rendering placeholder</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Right Column - Summary Panel (30%) */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-2xl font-semibold">Concept Summary</CardTitle>
            <CardDescription>
              Details for the selected node: <span className="font-semibold text-primary">{selectedNode.title}</span>
            </CardDescription>
          </CardHeader>
          <CardContent className="h-[calc(100%-100px)]">
            <ScrollArea className="h-full pr-4">
              <div className="space-y-6 text-sm">
                {/* Description Section */}
                <div>
                  <h3 className="font-semibold text-base mb-2 text-foreground">Description</h3>
                  <p className="text-muted-foreground leading-relaxed">
                    {selectedNode.description}
                  </p>
                </div>
                
                {/* Relationships Section */}
                <div>
                  <h3 className="font-semibold text-base mb-2 text-foreground">Key Relationships</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedNode.relationships.map((rel, index) => (
                      <Badge key={index} variant="secondary">{rel}</Badge>
                    ))}
                  </div>
                </div>

                {/* Related Concepts Section */}
                <div>
                  <h3 className="font-semibold text-base mb-2 text-foreground">Related Concepts</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedNode.relatedConcepts.map((concept, index) => (
                      <Badge key={index} variant="secondary">{concept}</Badge>
                    ))}
                  </div>
                </div>
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default KnowledgeGraph;