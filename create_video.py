// components/ReelHistory.tsx

import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ExternalLink, PlayCircle } from "lucide-react";

type ReelItem = {
  category: string;
  language: string;
  duration: string;
  created_at: string;
  drive_url?: string;
  instagram_url?: string;
};

type ReelHistoryProps = {
  reels: ReelItem[];
};

const ReelHistory: React.FC<ReelHistoryProps> = ({ reels }) => {
  if (!reels || reels.length === 0) {
    return <p className="text-center text-gray-500">No reels generated yet.</p>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {reels.map((reel, idx) => (
        <Card key={idx} className="rounded-2xl shadow-md p-3">
          <CardContent className="space-y-2">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold capitalize">{reel.category}</h3>
              <span className="text-sm text-gray-400">{reel.language.toUpperCase()}</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Duration: {reel.duration} | Created: {new Date(reel.created_at).toLocaleDateString()}
            </p>
            <div className="flex gap-2">
              {reel.drive_url && (
                <Button variant="secondary" asChild>
                  <a href={reel.drive_url} target="_blank" rel="noopener noreferrer">
                    <PlayCircle className="mr-1 w-4 h-4" />
                    Drive
                  </a>
                </Button>
              )}
              {reel.instagram_url && (
                <Button variant="outline" asChild>
                  <a href={reel.instagram_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="mr-1 w-4 h-4" />
                    Instagram
                  </a>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default ReelHistory;
