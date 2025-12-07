"use client";

import type { AttachmentResponse } from "@/lib/types/api";

interface AttachmentListProps {
  attachments: AttachmentResponse[];
  onDownload: (attachment: AttachmentResponse) => void;
  onDelete: (attachment: AttachmentResponse) => void;
  isLoading?: boolean;
}

export function AttachmentList({
  attachments,
  onDownload,
  onDelete,
  isLoading,
}: AttachmentListProps) {
  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (contentType: string) => {
    if (contentType.startsWith("image/")) return "🖼️";
    if (contentType.startsWith("video/")) return "🎥";
    if (contentType.startsWith("audio/")) return "🎵";
    if (contentType.includes("pdf")) return "📄";
    if (contentType.includes("word") || contentType.includes("document")) return "📝";
    if (contentType.includes("excel") || contentType.includes("spreadsheet")) return "📊";
    if (contentType.includes("powerpoint") || contentType.includes("presentation")) return "📽️";
    if (contentType.includes("zip") || contentType.includes("archive")) return "🗜️";
    return "📎";
  };

  const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  if (attachments.length === 0 && !isLoading) {
    return (
      <div className="text-center py-8 text-gray-500">
        <svg
          className="mx-auto h-12 w-12 text-gray-400 mb-3"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
          />
        </svg>
        <p className="text-sm">No files attached yet</p>
        <p className="text-xs text-gray-400 mt-1">Upload files to get started</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {attachments.map((attachment) => (
        <div
          key={attachment.id}
          className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-sm transition-all"
        >
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            {/* File Icon */}
            <div className="text-3xl flex-shrink-0">
              {getFileIcon(attachment.content_type)}
            </div>

            {/* File Info */}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate" title={attachment.filename}>
                {attachment.filename}
              </p>
              <div className="flex items-center space-x-3 text-xs text-gray-500 mt-1">
                <span>{formatFileSize(attachment.size_bytes)}</span>
                <span>•</span>
                <span>{formatDate(attachment.created_at)}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2 ml-4 flex-shrink-0">
            <button
              onClick={() => onDownload(attachment)}
              className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
              title="Download"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
            </button>
            <button
              onClick={() => onDelete(attachment)}
              disabled={isLoading}
              className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
              title="Delete"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
