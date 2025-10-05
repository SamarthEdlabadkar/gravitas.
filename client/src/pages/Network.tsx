import { ArrowLeft, ExternalLink, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNavigate, useLocation } from "react-router-dom";
import RadialNetworkGraph from "@/components/D3Graph";
import { useState, useMemo } from "react";

type Publication = {
  pmc_id: string;
  title: string;
  authors: string;
  journal: string;
  link: string;
  year: number;
  abstract: string;
  categories: string[];
};

const truncateText = (text: string, wordLimit: number) => {
  const words = text.split(" ");
  if (words.length > wordLimit) {
    return words.slice(0, wordLimit).join(" ") + " ...";
  }
  return text;
};


const Network = () => {
  const navigate = useNavigate();
  const location = useLocation();


  const publications = location.state?.results || [];
  const query = location.state?.query || "your query";

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const filteredPublications = useMemo(() => {
    // If no category is selected, show all publications
    if (!selectedCategory) {
      return publications;
    }

    
    // Otherwise, only show publications that include the selected category
    return publications.filter(pub =>
      pub.categories.includes(selectedCategory)
    );
  }, [selectedCategory, publications]);

  const handlePublicationClick = (publication: Publication) => {
    navigate("/knowledgegraph", { state: { publication, query } });
  };

  return (
    <div className="min-h-screen w-full p-6">
      {/* Header with Back Button */}
      <div className="max-w-[1600px] mx-auto mb-6">
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="gap-2 hover:bg-card/50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Button>
      </div>

      {/* Main Content */}
      <div className="max-w-[1600px] mx-auto grid lg:grid-cols-[60%_40%] gap-6">
        {/* Left Section - Knowledge Graph */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-[calc(100vh-140px)]">
          <CardContent className="h-[calc(100%)]">
            <RadialNetworkGraph onNodeClick={setSelectedCategory} />
          </CardContent>
        </Card>

        {/* Right Section - Publications List */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-[calc(100vh-140px)]">
          <CardHeader>
            <CardTitle className="text-3xl font-semibold">Related Publications</CardTitle>
            {selectedCategory ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>Filtering by: <span className="font-semibold text-primary">{selectedCategory}</span></span>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5"
                  onClick={() => setSelectedCategory(null)}
                >
                  <XCircle className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <CardDescription>Research papers matching: "{query}"</CardDescription>
            )}
          </CardHeader>
          <CardContent className="h-[calc(100%-100px)]">
            <ScrollArea className="h-full pr-4">
              <div className="space-y-4">
                {filteredPublications.map((pub: Publication) => (
                  <div
                    key={pub.pmc_id}
                    className="p-4 bg-background/50 border border-border/50 rounded-lg hover:border-primary/50 transition-all duration-200 hover:shadow-lg group"
                    onClick={() => handlePublicationClick(pub)}
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">
                        {pub.title}
                      </h3>
                      {/* Wrap the icon in its own link to preserve external navigation */}
                      <a
                        href={pub.link || `https://www.ncbi.nlm.nih.gov/pmc/articles/${pub.pmc_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()} // Stop the parent div's onClick from firing
                        className="flex-shrink-0"
                      >
                        <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                      </a>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {truncateText(pub.authors, 10)} • {pub.year}
                    </p>
                    <p className="text-sm text-muted-foreground/80 leading-relaxed">
                      {truncateText(pub.abstract, 20)}
                    </p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Network;