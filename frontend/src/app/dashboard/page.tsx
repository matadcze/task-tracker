"use client";

import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api/client";
import { TaskPriority, TaskStatus } from "@/lib/types/api";
import type {
  TaskResponse,
  TaskCreate,
  TaskUpdate,
  TaskDetailResponse,
} from "@/lib/types/api";
import { getFriendlyErrorMessage } from "@/lib/utils/error";
import { TaskCard } from "@/components/tasks/TaskCard";
import { TaskForm } from "@/components/tasks/TaskForm";
import { TaskDetails } from "@/components/tasks/TaskDetails";
import { DeleteConfirmModal } from "@/components/tasks/DeleteConfirmModal";
import { SearchAndFilters } from "@/components/tasks/SearchAndFilters";
import { Pagination } from "@/components/common/Pagination";
import { Modal } from "@/components/common/Modal";
import { TaskAssistant } from "@/components/assistant/TaskAssistant";

export default function DashboardPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const router = useRouter();

  // State
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [totalTasks, setTotalTasks] = useState(0);

  // Search and Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null);
  const [selectedTaskDetail, setSelectedTaskDetail] = useState<TaskDetailResponse | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      fetchTasks();
    }
  }, [user, currentPage, pageSize, searchQuery, statusFilter, priorityFilter, sortBy, sortOrder]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError("");
      const response = await apiClient.tasks.list({
        page: currentPage,
        page_size: pageSize,
        search: searchQuery || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      setTasks(response.items);
      setTotalTasks(response.total);
    } catch (err) {
      setError(getFriendlyErrorMessage(err, "Failed to load tasks. Please try again."));
      console.error("Fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTaskDetails = async (taskId: string) => {
    try {
      const detail = await apiClient.tasks.get(taskId);
      setSelectedTaskDetail(detail);
      setIsDetailsModalOpen(true);
    } catch (err) {
      setError(getFriendlyErrorMessage(err, "Failed to load task details."));
      console.error("Fetch details error:", err);
    }
  };

  const handleCreateTask = async (data: TaskCreate | TaskUpdate) => {
    try {
      setActionLoading(true);
      await apiClient.tasks.create(data as TaskCreate);
      setIsCreateModalOpen(false);
      fetchTasks();
    } catch (err) {
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateTask = async (data: TaskUpdate) => {
    if (!selectedTask) return;

    try {
      setActionLoading(true);
      await apiClient.tasks.update(selectedTask.id, data);
      setIsEditModalOpen(false);
      setSelectedTask(null);
      fetchTasks();
      if (selectedTaskDetail) {
        fetchTaskDetails(selectedTask.id);
      }
    } catch (err) {
      throw err;
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteTask = async () => {
    if (!selectedTask) return;

    try {
      setActionLoading(true);
      await apiClient.tasks.delete(selectedTask.id);
      setIsDeleteModalOpen(false);
      setIsDetailsModalOpen(false);
      setSelectedTask(null);
      setSelectedTaskDetail(null);
      fetchTasks();
    } catch (err) {
      setError(getFriendlyErrorMessage(err, "Failed to delete task. Please try again."));
      console.error("Delete error:", err);
    } finally {
      setActionLoading(false);
    }
  };

  const openEditModal = (task: TaskResponse) => {
    setSelectedTask(task);
    setIsEditModalOpen(true);
  };

  const openDeleteModal = (task: TaskResponse) => {
    setSelectedTask(task);
    setIsDeleteModalOpen(true);
  };

  const handleClearFilters = () => {
    setSearchQuery("");
    setStatusFilter("");
    setPriorityFilter("");
    setSortBy("created_at");
    setSortOrder("desc");
    setCurrentPage(1);
  };

  const totalPages = Math.ceil(totalTasks / pageSize);

  if (authLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const openTasks = tasks.filter((task) => task.status !== TaskStatus.DONE).length;
  const highPriority = tasks.filter((task) => task.priority === TaskPriority.HIGH).length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      <header className="bg-white/80 backdrop-blur border-b border-indigo-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-indigo-500 font-semibold">Dashboard</p>
            <h1 className="text-4xl text-display font-ultra-bold text-gray-900 tracking-tight mt-1">
              Task Tracker
            </h1>
            <p className="text-sm font-light text-gray-600 tracking-wide mt-1">
              Welcome, {user.full_name || user.email}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/profile"
              className="px-4 py-2 text-sm font-bold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 tracking-wide"
            >
              Profile
            </Link>
            <button
              onClick={logout}
              className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 tracking-wide"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-md shadow-sm">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="bg-white shadow rounded-xl p-6 border border-indigo-50 flex flex-col gap-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-indigo-500 font-semibold">
                    Tasks
                  </p>
                  <h2 className="text-2xl font-ultra-bold text-gray-900 tracking-tight">
                    Your workbench
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    Filter, sort, and manage everything in one place.
                  </p>
                </div>
                <button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 tracking-wide"
                >
                  + New Task
                </button>
              </div>

              <div className="rounded-lg border border-gray-100 bg-gray-50/80 p-4">
                <SearchAndFilters
                  searchQuery={searchQuery}
                  onSearchChange={setSearchQuery}
                  status={statusFilter}
                  onStatusChange={setStatusFilter}
                  priority={priorityFilter}
                  onPriorityChange={setPriorityFilter}
                  sortBy={sortBy}
                  onSortByChange={setSortBy}
                  sortOrder={sortOrder}
                  onSortOrderChange={setSortOrder}
                  onClearFilters={handleClearFilters}
                />
              </div>
            </div>

            {loading ? (
              <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
              </div>
            ) : tasks.length === 0 ? (
              <div className="bg-white rounded-xl shadow border border-indigo-50 p-12 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                  />
                </svg>
                <h3 className="mt-2 text-2xl text-display font-ultra-bold text-gray-900 tracking-tight">
                  No tasks
                </h3>
                <p className="mt-1 text-sm font-light text-gray-500 tracking-wide">
                  Get started by creating a new task.
                </p>
                <div className="mt-6">
                  <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="px-4 py-2 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md tracking-wide"
                  >
                    + New Task
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow border border-indigo-50 p-4 md:p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {tasks.map((task) => (
                    <TaskCard
                      key={task.id}
                      task={task}
                      onEdit={openEditModal}
                      onDelete={openDeleteModal}
                      onViewDetails={() => fetchTaskDetails(task.id)}
                    />
                  ))}
                </div>

                <Pagination
                  currentPage={currentPage}
                  totalPages={totalPages}
                  totalItems={totalTasks}
                  pageSize={pageSize}
                  onPageChange={setCurrentPage}
                  onPageSizeChange={(size) => {
                    setPageSize(size);
                    setCurrentPage(1);
                  }}
                />
              </div>
            )}
          </div>

          <aside className="space-y-4">
            <TaskAssistant
              onTaskCreated={async () => {
                await fetchTasks();
              }}
            />
            <div className="bg-white shadow rounded-xl p-5 border border-indigo-50">
              <p className="text-xs uppercase tracking-[0.3em] text-indigo-500 font-semibold">
                Snapshot
              </p>
              <h3 className="text-xl font-ultra-bold text-gray-900 tracking-tight mt-1">
                Today&apos;s focus
              </h3>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between rounded-lg border border-gray-100 p-3">
                  <div>
                    <p className="text-sm text-gray-600">Total tasks</p>
                    <p className="text-2xl font-bold text-gray-900">{totalTasks}</p>
                  </div>
                  <span className="px-3 py-1 text-xs font-semibold bg-indigo-100 text-indigo-700 rounded-full">
                    All
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg border border-gray-100 p-3">
                  <div>
                    <p className="text-sm text-gray-600">Open</p>
                    <p className="text-xl font-bold text-gray-900">{openTasks}</p>
                  </div>
                  <span className="px-3 py-1 text-xs font-semibold bg-amber-100 text-amber-700 rounded-full">
                    Pending
                  </span>
                </div>
                <div className="flex items-center justify-between rounded-lg border border-gray-100 p-3">
                  <div>
                    <p className="text-sm text-gray-600">High priority</p>
                    <p className="text-xl font-bold text-gray-900">{highPriority}</p>
                  </div>
                  <span className="px-3 py-1 text-xs font-semibold bg-rose-100 text-rose-700 rounded-full">
                    Important
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 text-white rounded-xl shadow p-5">
              <h3 className="text-xl font-ultra-bold tracking-tight">Stay organized</h3>
              <p className="text-sm text-indigo-100 mt-2">
                Use tags and priorities to triage your work. Filter by what matters and keep the flow.
              </p>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="mt-4 inline-flex items-center justify-center px-3 py-2 text-sm font-bold bg-white text-indigo-700 rounded-md shadow hover:bg-indigo-50"
              >
                Add a task
              </button>
            </div>
          </aside>
        </div>
      </main>

      {/* Create Task Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Task"
        size="lg"
      >
        <TaskForm
          onSubmit={handleCreateTask}
          onCancel={() => setIsCreateModalOpen(false)}
          isLoading={actionLoading}
        />
      </Modal>

      {/* Edit Task Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setSelectedTask(null);
        }}
        title="Edit Task"
        size="lg"
      >
        {selectedTask && (
          <TaskForm
            task={selectedTask}
            onSubmit={handleUpdateTask}
            onCancel={() => {
              setIsEditModalOpen(false);
              setSelectedTask(null);
            }}
            isLoading={actionLoading}
          />
        )}
      </Modal>

      {/* Task Details Modal */}
      <Modal
        isOpen={isDetailsModalOpen}
        onClose={() => {
          setIsDetailsModalOpen(false);
          setSelectedTaskDetail(null);
        }}
        title="Task Details"
        size="xl"
      >
        {selectedTaskDetail && (
          <TaskDetails
            taskDetail={selectedTaskDetail}
            onEdit={() => {
              setSelectedTask(selectedTaskDetail.task);
              setIsDetailsModalOpen(false);
              setIsEditModalOpen(true);
            }}
            onDelete={() => {
              setSelectedTask(selectedTaskDetail.task);
              setIsDeleteModalOpen(true);
            }}
            onRefresh={() => fetchTaskDetails(selectedTaskDetail.task.id)}
          />
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => {
          setIsDeleteModalOpen(false);
          setSelectedTask(null);
        }}
        onConfirm={handleDeleteTask}
        itemName={selectedTask?.title || "this task"}
        isLoading={actionLoading}
      />
    </div>
  );
}
