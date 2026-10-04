import { ImageResponse } from "next/og";

export const size = { width: 180, height: 180 };
export const contentType = "image/png";

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", background: "#0f0d0e", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ width: 104, height: 104, borderRadius: 52, border: "11px solid #ff9147", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "flex-end", overflow: "hidden" }}>
          <div style={{ width: 30, height: 30, borderRadius: 15, background: "#f4efee", marginBottom: 6 }} />
          <div style={{ width: 62, height: 26, borderTopLeftRadius: 31, borderTopRightRadius: 31, background: "#f4efee" }} />
        </div>
      </div>
    ),
    size,
  );
}
