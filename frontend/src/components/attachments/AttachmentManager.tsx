"use client";

import { useState } from "react";
import type { AttachmentResponse } from "@/lib/types/api";
import { FileUploadZone } from "./FileUploadZone";
import { AttachmentList } from "./AttachmentList";
import { apiClient } from "@/lib/api/client";

interface AttachmentManagerProps {
  taskId: string;
  attachments: AttachmentResponse[];
  onRefresh: () => void;
}

export function AttachmentManager({ taskId, attachments, onRefresh }: AttachmentManagerProps) {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const totalSize = attachments.reduce((acc, file) => acc + file.size_bytes, 0);
  const latestUpload = attachments
    .map((file) => new Date(file.created_at).getTime())
    .sort((a, b) => b - a)[0];

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const handleFileSelect = async (file: File) => {
    setUploading(true);
    setUploadProgress(0);
    setError("");

    try {
      // Simulate progress (since we can't track actual upload progress easily)
      setUploadProgress(30);

      await apiClient.attachments.upload(taskId, file);

      setUploadProgress(100);
      setTimeout(() => {
        setUploadProgress(0);
        setUploading(false);
        onRefresh();
      }, 500);
    } catch (err: any) {
      console.error("Upload error:", err);
      setError(err?.message || "Failed to upload file. Please try again.");
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleDownload = (attachment: AttachmentResponse) => {
    const downloadUrl = apiClient.attachments.download(taskId, attachment.id);
    window.open(downloadUrl, "_blank");
  };

  const handleDelete = async (attachment: AttachmentResponse) => {
    if (!confirm(`Are you sure you want to delete "${attachment.filename}"?`)) {
      return;
    }

    setDeleting(attachment.id);
    setError("");

    try {
      await apiClient.attachments.delete(taskId, attachment.id);
      onRefresh();
    } catch (err: any) {
      console.error("Delete error:", err);
      setError(err?.message || "Failed to delete file. Please try again.");
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="space-y-4 rounded-lg border border-gray-100 bg-white p-5 shadow-sm">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.25em] text-gray-500 font-semibold">
            Attachments
          </p>
          <h3 className="text-xl font-ultra-bold text-gray-900 leading-tight">Files</h3>
          <p className="text-sm text-gray-500 mt-0.5">
            {attachments.length} {attachments.length === 1 ? "file" : "files"} ·{" "}
            {formatFileSize(totalSize)}
            {latestUpload ? ` · Updated ${new Date(latestUpload).toLocaleDateString()}` : ""}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 border border-gray-100 px-3 py-2 rounded-md">
          <span className="h-2 w-2 rounded-full bg-indigo-500" />
          Drag & drop or click to add more files
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Upload Zone */}
      <div className="rounded-md border border-dashed border-gray-200 bg-gray-50/60 p-4">
        <FileUploadZone onFileSelect={handleFileSelect} disabled={uploading} />

        {/* Upload Progress */}
        {uploading && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
              <span>Uploading...</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* File List */}
      <AttachmentList
        attachments={attachments}
        onDownload={handleDownload}
        onDelete={handleDelete}
        isLoading={!!deleting}
      />
    </div>
  );
}
