"use client";

import React, { useEffect, useState } from "react";
import QRCode from "qrcode";
import { Loader2 } from "lucide-react";

interface QRCodeViewProps {
  value: string;
  size?: number;
  className?: string;
}

export function QRCodeView({ value, size = 180, className }: QRCodeViewProps) {
  const [dataUrl, setDataUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!value) return;
    setLoading(true);
    QRCode.toDataURL(value, {
      width: size,
      margin: 1.5,
      color: {
        dark: "#1e1b4b",
        light: "#ffffff",
      },
    })
      .then((url) => {
        setDataUrl(url);
      })
      .catch((err) => {
        console.error("QR Code generation error:", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [value, size]);

  if (loading) {
    return (
      <div
        style={{ width: size, height: size }}
        className="flex items-center justify-center bg-slate-100 dark:bg-slate-800 rounded-xl"
      >
        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!dataUrl) {
    return <div className="text-xs text-rose-500">Failed to render QR</div>;
  }

  return (
    <div className="p-2 bg-white rounded-2xl shadow-sm border border-slate-200 inline-block">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={dataUrl}
        alt="QR Code"
        width={size}
        height={size}
        className={className}
      />
    </div>
  );
}
