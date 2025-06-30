// components/ReelHistory.jsx

import React, { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { ExternalLink } from "lucide-react";
import moment from "moment";

const ReelHistory = ({ username }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!username) return;

    const fetchHistory = async () => {
      try {
        const res = await fetch(`/reel-history/${username}`);
        const json = await res.json();
        const sorted = json?.history?.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        setHistory(sorted);
      } catch (err) {
        console.error("Failed to load history", err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [username]);

  if (loading) return <div className="text-center py-10">Loading history...</div>;

  if (!history?.length)
    return <div className="text-center py-10 text-gray-500">No reels posted yet.</div>;

  return (
    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
      {history.map((item, i) => (
        <Card key={i} className="rounded-2xl shadow-md p-4">
          <CardContent>
            <div className="text-sm text-gray-400 mb-2">
              {moment(item.timestamp).fromNow()}
            </div>
            <div className="text-xl font-semibold capitalize mb-2">
              {item.category.replace(/_/g, " ")}
            </div>
            <a
              href={item.permalink}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline flex items-center gap-1 text-sm"
            >
              View on Instagram <ExternalLink size={14} />
            </a>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

export default ReelHistory;
