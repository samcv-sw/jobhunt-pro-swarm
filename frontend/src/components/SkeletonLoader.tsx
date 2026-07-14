import React from 'react';

interface SkeletonLoaderProps {
  className?: string;
  width?: string;
  height?: string;
  borderRadius?: string;
}

export function SkeletonLoader({
  className = '',
  width = '100%',
  height = '20px',
  borderRadius = '4px',
}: SkeletonLoaderProps) {
  return (
    <div
      className={`animate-pulse bg-[#1a1a24] ${className}`}
      style={{
        inlineSize: width,
        blockSize: height,
        borderRadius,
      }}
      aria-hidden="true"
    />
  );
}

export function SkeletonProfile() {
  return (
    <div className="flex flex-row items-center gap-4 p-4" style={{ inlineSize: "100%" }}>
      <SkeletonLoader width="50px" height="50px" borderRadius="50%" />
      <div className="flex flex-col gap-2 flex-grow">
        <SkeletonLoader width="60%" height="16px" />
        <SkeletonLoader width="40%" height="12px" />
      </div>
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="flex flex-col gap-4 p-4 bg-[#0a0a0f] rounded-lg border border-[#1a1a24]" style={{ inlineSize: "100%" }}>
      <SkeletonLoader width="100%" height="120px" borderRadius="8px" />
      <SkeletonLoader width="80%" height="20px" />
      <SkeletonLoader width="60%" height="16px" />
    </div>
  );
}
