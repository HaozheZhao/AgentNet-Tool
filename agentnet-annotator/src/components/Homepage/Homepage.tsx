import { useEffect, useState } from "react";
import { Snackbar } from "@mui/joy";
import { PlayIcon } from "@heroicons/react/24/outline";
import { useMain } from "../../context/MainContext";
import TaskHubModal from "../TaskHub/TaskHubModal";
import { StopIcon } from "@heroicons/react/24/solid";
import AutoFixHighIcon from "@mui/icons-material/AutoFixHigh";
export default function Homepage() {
    const [openSnackbar, setOpenSnackbar] = useState(false);
    const [openTaskHub, setOpenTaskHub] = useState(false);
    const [message, setMessage] = useState("");
    const [severity, setSeverity] = useState("success");
    const [genWindowA11y, setGenWindowA11y] = useState(false);
    const {
        isRecording,
        setIsRecording,
        SocketService,
        username,
        fetchTasks,
        addNewRecording,
        HubTaskId,
        setHubTaskId,
        HubTaskName,
        setHubTaskName,
        setHubTaskDescription,
        HubTaskDescription,
        myos,
        userData,
    } = useMain();
    const [loading, setLoading] = useState(false);

    const handleRecordClick = () => {
        if (!loading) {
            ToggleRecord(); // 假设这个函数会处理录制逻辑
        }
    };
    const showSuccess = (message: string) => {
        setOpenSnackbar(true);
        setMessage(message);
        setSeverity("success");
        setTimeout(() => {
            setOpenSnackbar(false);
        }, 3000);
    };

    const showError = (message: string) => {
        setOpenSnackbar(true);
        setMessage(message);
        setSeverity("warning");
        setTimeout(() => {
            setOpenSnackbar(false);
        }, 3000);
    };

    const ToggleRecord = () => {
        // Removed login checks - allow recording without authentication
        setLoading(true);
        console.log(username);
        if (!isRecording) {
            window.electron.ipcRenderer.sendMessage("start-record-icon");
            SocketService.GetWithParams("start_record", {
                task_hub_data: {
                    hub_task_id: HubTaskId,
                    hub_task_name: HubTaskName,
                    hub_task_description: HubTaskDescription,
                },
            })
                .then((data) => {
                    console.log("Operation succeeded:", data);
                    showSuccess(data.message);
                    setIsRecording(true);
                    setLoading(false);
                    setTimeout(() => {
                        window.electron.ipcRenderer.sendMessage(
                            "minimize-window"
                        );
                    }, 1500);
                    setHubTaskId("");
                    setHubTaskName("");
                    setHubTaskDescription("");
                })
                .catch((error) => {
                    console.error("Operation failed:", error.message);
                    showError(error.message);
                    // 请求失败后也停止loading
                    setLoading(false);
                    setTimeout(() => {
                        window.location.reload();
                    }, 3000);
                });
            } else {
                console.log("Stop Recording");
                window.electron.ipcRenderer.sendMessage("stop-record-icon");
                SocketService.Get("stop_record")
                    .then(async (data) => {
                        console.log("Operation succeeded:", data);
                        setIsRecording(false);
                        setLoading(false);
                        
                        // Try to fetch tasks from backend, if fails use fallback
                        try {
                            await fetchTasks();
                        } catch (fetchError) {
                            console.log("fetchTasks failed, adding recording manually");
                            addNewRecording();
                        }
                    })
                    .catch((error) => {
                        console.error("Operation failed:", error.message);
                        showError(error.message);
                        setLoading(false);
                        setIsRecording(false);
                        
                        // Even if stop_record fails, try to add the recording manually
                        addNewRecording();
                    });
        }
    };

    const handleWindowA11yChange = () => {
        SocketService.Send("toggle_generate_window_a11y", {
            flag: !genWindowA11y,
        });
        setGenWindowA11y(!genWindowA11y);
    };
    useEffect(() => {
        SocketService.Send("toggle_generate_window_a11y", {
            flag: false,
        });
        setGenWindowA11y(false);
    }, []);

    const handleOpenTaskHub = () => {
        setOpenTaskHub(true);
    };

    const handleCloseTaskHub = () => {
        setOpenTaskHub(false);
    };

    return (
        <div className="min-h-screen w-full bg-gradient-to-br from-slate-50 via-white to-indigo-50 dark:from-gray-950 dark:via-gray-900 dark:to-indigo-950">
            {/* Decorative background blobs */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
                <div className="absolute -top-24 -left-24 w-96 h-96 bg-indigo-400/20 rounded-full blur-3xl" />
                <div className="absolute top-1/3 -right-24 w-80 h-80 bg-violet-400/15 rounded-full blur-3xl" />
                <div className="absolute -bottom-24 left-1/3 w-72 h-72 bg-blue-400/10 rounded-full blur-3xl" />
            </div>

            <div className="relative z-10 flex flex-col items-center px-6 pt-16 pb-24 sm:pt-24">
                {/* Title */}
                <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-gradient mb-4">
                    CCAgent
                </h1>
                <p className="max-w-lg text-center text-base text-gray-500 dark:text-gray-400 mb-12">
                    A customized toolkit for labeling agent task data for collection.
                </p>

                {/* Task info banner */}
                {(HubTaskName || HubTaskDescription) && (
                    <div className="w-full max-w-lg mb-8">
                        <div className="glass-card rounded-2xl p-5 shadow-lg">
                            <h2 className="text-sm font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400 mb-1">
                                Current Task
                            </h2>
                            {HubTaskName && (
                                <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                                    {HubTaskName}
                                </p>
                            )}
                            {HubTaskDescription && (
                                <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                                    {HubTaskDescription}
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {/* Recording button — large, centered, prominent */}
                <div className="w-full max-w-lg mb-6">
                    <div
                        id="recording"
                        className={`glass-card rounded-2xl p-6 cursor-pointer transition-all duration-300 ease-out
                            ${isRecording
                                ? "ring-2 ring-red-500 shadow-lg shadow-red-200/40 dark:shadow-red-900/30"
                                : "shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                            }
                            ${loading ? "opacity-60 cursor-not-allowed" : ""}`}
                        onClick={handleRecordClick}
                    >
                        <div className="flex items-center gap-5">
                            {/* Icon circle */}
                            <div
                                className={`flex-shrink-0 flex h-14 w-14 items-center justify-center rounded-2xl transition-all duration-300
                                    ${isRecording
                                        ? "bg-red-500 animate-pulse-ring"
                                        : "bg-gradient-to-br from-indigo-500 to-violet-600"
                                    }`}
                            >
                                {loading ? (
                                    <div
                                        className="animate-spin inline-block size-7 border-[3px] border-white border-t-transparent rounded-full"
                                        role="status"
                                        aria-label="loading"
                                    >
                                        <span className="sr-only">Loading...</span>
                                    </div>
                                ) : isRecording ? (
                                    <StopIcon className="h-7 w-7 text-white" aria-hidden="true" />
                                ) : (
                                    <PlayIcon className="h-7 w-7 text-white" aria-hidden="true" />
                                )}
                            </div>

                            {/* Text + shortcut */}
                            <div className="flex-1 min-w-0">
                                <p className={`text-xl font-bold ${isRecording ? "text-red-600 dark:text-red-400" : "text-gray-900 dark:text-gray-100"}`}>
                                    {loading ? "Processing..." : isRecording ? "Stop Recording" : "Start Recording"}
                                </p>
                                {!loading && (
                                    <div className="flex items-center gap-1.5 mt-1.5">
                                        {myos === "darwin" ? (
                                            <>
                                                <kbd className="inline-flex items-center justify-center h-7 min-w-[28px] px-1.5 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-xs font-mono text-gray-600 dark:text-gray-300 shadow-sm">
                                                    <svg className="shrink-0 size-3" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 6v12a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3"></path></svg>
                                                </kbd>
                                                <span className="text-gray-400 text-xs">+</span>
                                                <kbd className="inline-flex items-center justify-center h-7 min-w-[28px] px-1.5 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-xs font-mono text-gray-600 dark:text-gray-300 shadow-sm">
                                                    <svg className="shrink-0 size-3" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3h6l6 18h6"></path><path d="M14 3h7"></path></svg>
                                                </kbd>
                                                <span className="text-gray-400 text-xs">+</span>
                                                <kbd className="inline-flex items-center justify-center h-7 min-w-[28px] px-1.5 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-xs font-mono text-gray-600 dark:text-gray-300 shadow-sm">
                                                    {isRecording ? "T" : "R"}
                                                </kbd>
                                            </>
                                        ) : (
                                            <>
                                                <kbd className="inline-flex items-center justify-center h-7 min-w-[28px] px-1.5 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-xs font-mono text-gray-600 dark:text-gray-300 shadow-sm">ctrl</kbd>
                                                <span className="text-gray-400 text-xs">+</span>
                                                <kbd className="inline-flex items-center justify-center h-7 min-w-[28px] px-1.5 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-xs font-mono text-gray-600 dark:text-gray-300 shadow-sm">alt</kbd>
                                                <span className="text-gray-400 text-xs">+</span>
                                                <kbd className="inline-flex items-center justify-center h-7 min-w-[28px] px-1.5 rounded-md bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-xs font-mono text-gray-600 dark:text-gray-300 shadow-sm">
                                                    {isRecording ? "T" : "R"}
                                                </kbd>
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Task Hub card */}
                <div className="w-full max-w-lg mb-8">
                    <div
                        className="glass-card rounded-2xl p-6 cursor-pointer transition-all duration-300 ease-out shadow-lg hover:shadow-xl hover:-translate-y-0.5"
                        onClick={() => handleOpenTaskHub()}
                    >
                        <div className="flex items-center gap-5">
                            <div className="flex-shrink-0 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 to-orange-500">
                                <AutoFixHighIcon
                                    aria-hidden="true"
                                    className="h-7 w-7"
                                    style={{ color: "white" }}
                                />
                            </div>
                            <div>
                                <p className="text-xl font-bold text-gray-900 dark:text-gray-100">Random Task</p>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                                    Randomly select a task from the task hub with detailed tutorial.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Accessibility checkbox */}
                <div className="w-full max-w-lg">
                    <label htmlFor="comments" className="flex items-center gap-3 cursor-pointer group">
                        <input
                            id="comments"
                            aria-describedby="comments-description"
                            name="comments"
                            type="checkbox"
                            className="h-5 w-5 rounded-md border-gray-300 text-indigo-600 focus:ring-indigo-500 transition-colors"
                            checked={genWindowA11y}
                            onChange={handleWindowA11yChange}
                        />
                        <div>
                            <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 transition-colors">
                                Get Accessibility Tree
                            </span>
                            <p
                                id="comments-description"
                                className="text-xs text-gray-400 dark:text-gray-500"
                            >
                                Capture the accessibility tree of the current window during recording.
                            </p>
                        </div>
                    </label>
                </div>
            </div>

            <Snackbar
                open={openSnackbar}
                autoHideDuration={5000}
                onClose={() => setOpenSnackbar(false)}
                anchorOrigin={{ vertical: "top", horizontal: "center" }}
                color={severity === "success" ? "success" : "warning"}
            >
                {message}
            </Snackbar>
            <TaskHubModal open={openTaskHub} onClose={handleCloseTaskHub} />
        </div>
    );
}
