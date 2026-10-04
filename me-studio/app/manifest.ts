import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Me Studio",
    short_name: "Me Studio",
    start_url: "/",
    display: "standalone",
    background_color: "#0f0d0e",
    theme_color: "#0f0d0e",
    icons: [
      { src: "/icon.svg", sizes: "any", type: "image/svg+xml" },
      { src: "/apple-icon", sizes: "180x180", type: "image/png" },
    ],
  };
}
