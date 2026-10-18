import { useEffect, useState } from "react";
import { getHealth } from "../services/api";

export function useBackendStatus() {
  const [status, setStatus] = useState("checking");
  const [health, setHealth] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function checkBackend() {
      try {
        const data = await getHealth();

        if (!mounted) return;

        setHealth(data);
        setStatus("online");
      } catch (error) {
        if (!mounted) return;

        setStatus("offline");
        setHealth(null);
      }
    }

    checkBackend();

    return () => {
      mounted = false;
    };
  }, []);

  return {
    status,
    health,
  };
}