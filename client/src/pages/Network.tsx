import { ArrowLeft, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useNavigate, useLocation } from "react-router-dom";
import RadialNetworkGraph from "@/components/D3Graph";

type Publication = {
  pmc_id: string;
  title: string;
  authors: string;
  year: number;
  abstract: string;
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

  // Placeholder publication data
  {/* 
  const publications = [
    {
      id: 1,
      title: "Effects of Microgravity on Human Bone Density",
      authors: "Smith, J., Johnson, A., Williams, R.",
      year: 2023,
      description: "A comprehensive study examining the long-term effects of spaceflight on bone mineral density in astronauts during extended missions."
    },
    {
      id: 2,
      title: "Cardiovascular Adaptations in Zero Gravity Environments",
      authors: "Chen, L., Kumar, P., Martinez, E.",
      year: 2022,
      description: "Investigation of cardiovascular system changes and adaptation mechanisms during prolonged exposure to microgravity conditions."
    },
    {
      id: 3,
      title: "Muscle Atrophy Prevention Strategies for Space Missions",
      authors: "Anderson, K., Brown, T., Lee, S.",
      year: 2023,
      description: "Analysis of exercise protocols and pharmaceutical interventions designed to mitigate muscle loss in spaceflight environments."
    },
    {
      id: 4,
      title: "Immune System Function During Extended Spaceflight",
      authors: "Davis, M., Wilson, N., Thompson, J.",
      year: 2022,
      description: "Study of immune response alterations and potential health risks for astronauts on long-duration space missions."
    },
    {
      id: 5,
      title: "Radiation Exposure and DNA Damage in Space Travelers",
      authors: "Garcia, R., Patel, V., Kim, H.",
      year: 2023,
      description: "Examination of cosmic radiation effects on cellular DNA and long-term health implications for human space exploration."
    },
    {
      id: 6,
      title: "Vestibular System Changes in Microgravity",
      authors: "White, D., Lewis, C., Taylor, B.",
      year: 2021,
      description: "Research on balance and spatial orientation adaptations during and after exposure to weightless conditions."
    }
  ];*/}

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
            <RadialNetworkGraph />
            {/* 
            <div className="w-full h-full bg-muted/20 rounded-lg border border-border/50 flex items-center justify-center">
              <div className="text-center space-y-2">
                <div className="w-24 h-24 mx-auto rounded-full bg-primary/10 flex items-center justify-center">
                  <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                    <div className="w-8 h-8 rounded-full bg-primary/40" />
                  </div>
                </div>
                <p className="text-muted-foreground text-lg">Radial Tree Visualization</p>
                <p className="text-muted-foreground/60 text-sm">Graph rendering placeholder</p>
              </div>
            </div>*/}
          </CardContent>
        </Card>

        {/* Right Section - Publications List */}
        <Card className="bg-card/50 backdrop-blur-sm border-border/50 h-[calc(100vh-140px)]">
          <CardHeader>
            <CardTitle className="text-3xl font-semibold">Related Publications</CardTitle>
            <CardDescription>Research papers matching: "{query}"</CardDescription>
          </CardHeader>
          <CardContent className="h-[calc(100%-100px)]">
            <ScrollArea className="h-full pr-4">
              <div className="space-y-4">
                {publications.map((pub: Publication) => (
                  <div
                    key={pub.pmc_id}
                    className="p-4 bg-background/50 border border-border/50 rounded-lg hover:border-primary/50 transition-all duration-200 hover:shadow-lg group cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="font-semibold text-lg group-hover:text-primary transition-colors">
                        {pub.title}
                      </h3>
                      <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">
                      {pub.authors} • {pub.year}
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