import { useMemo, useState } from 'react';

import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { getProjectWorkspace, listProjects } from '../../api/projects';
import { listReports } from '../../api/reports';
import { getSystemStatus } from '../../api/system';
import { EmptyState } from '../../components/common/EmptyState';
import { SelectionList } from '../../components/common/SelectionList';
import { StatusPill } from '../../components/common/StatusPill';
import { setWorkflowSelection, useWorkflowSelection } from '../../features/workflow/state';
import { formatDateTime, truncateMiddle } from '../../lib/format';
import { findProjectRecord } from '../../lib/platform';

type ProjectViewMode = 'overview' | 'reports' | 'runtime';

function planningModeLabel(mode: string) {
  if (mode === 'single_scenario') {
    return '单场景';
  }
  if (mode === 'timed_single_scenario') {
    return '长时单场景';
  }
  if (mode === 'all_runnable') {
    return '全量回归';
  }
  return '自定义批量';
}

function canArchiveReport(status: string) {
  return ['COMPLETED', 'PARTIAL_FAILED', 'FAILED', 'CANCELED'].includes(status);
}

function isActiveTask(status: string) {
  return ['CREATED', 'RUNNING'].includes(status);
}

export function ProjectsPage() {
  const workflow = useWorkflowSelection();
  const [viewMode, setViewMode] = useState<ProjectViewMode>('overview');

  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: listProjects });
  const systemQuery = useQuery({
    queryKey: ['system-status'],
    queryFn: getSystemStatus,
    refetchInterval: 3000
  });

  const projects = projectsQuery.data ?? [];
  const selectedProject = workflow.projectId ? findProjectRecord(projects, workflow.projectId) : null;

  const workspaceQuery = useQuery({
    queryKey: ['projects', workflow.projectId, 'workspace'],
    queryFn: () => getProjectWorkspace(workflow.projectId ?? ''),
    enabled: Boolean(workflow.projectId)
  });
  const reportsQuery = useQuery({
    queryKey: ['reports', workflow.projectId],
    queryFn: () => listReports({ projectId: workflow.projectId ?? '' }),
    enabled: Boolean(workflow.projectId),
    refetchInterval: 5000
  });

  const workspace = workspaceQuery.data;
  const reports = reportsQuery.data ?? [];
  const reportedTaskIds = useMemo(
    () => new Set(reports.map((report) => report.benchmark_task_id)),
    [reports]
  );

  const latestReport = reports[0] ?? null;
  const latestTask = workspace?.benchmark_tasks[0] ?? null;
  const latestRun = workspace?.recent_runs[0] ?? null;
  const activeTaskCount = workspace?.benchmark_tasks.filter((task) => isActiveTask(task.status)).length ?? 0;
  const archivableTaskCount =
    workspace?.benchmark_tasks.filter((task) => canArchiveReport(task.status)).length ?? 0;
  const pendingReportTasks =
    workspace?.benchmark_tasks.filter(
      (task) => canArchiveReport(task.status) && !reportedTaskIds.has(task.benchmark_task_id)
    ) ?? [];

  return (
    <div className="page-stack">
      <section className="project-console">
        <header className="project-console__header">
          <div>
            <span className="project-console__eyebrow">场景控制层 / 项目工作台</span>
            <h1>项目归档台</h1>
            <p>项目页只负责项目总览、报告归档和运行态汇总，不再重复展开基准任务编排和场景模板参数。</p>
          </div>

          <div className="project-console__header-actions">
            <Link className="horizon-button-secondary" to="/reports" viewTransition>
              打开报告中心
            </Link>
            <Link className="horizon-button" to="/benchmarks" viewTransition>
              去创建基准任务
            </Link>
          </div>
        </header>

        <div className="project-console__layout">
          <aside className="project-console__rail">
            <section className="project-console__card">
              <header className="project-console__card-header">
                <div>
                  <span className="project-console__section-label">项目入口</span>
                  <strong>项目列表</strong>
                </div>
              </header>

              {projectsQuery.isLoading ? (
                <EmptyState description="正在同步项目目录。" title="项目加载中" />
              ) : projectsQuery.isError ? (
                <EmptyState
                  description={
                    projectsQuery.error instanceof Error ? projectsQuery.error.message : '项目接口异常。'
                  }
                  title="项目加载失败"
                />
              ) : (
                <SelectionList
                  emptyDescription="后端暂未返回项目记录。"
                  emptyTitle="没有项目"
                  expandLabel="展开项目"
                  maxVisible={6}
                  items={projects.map((project) => ({
                    id: project.project_id,
                    title: project.name,
                    subtitle: project.description,
                    meta: `${project.vendor} / ${project.processor}`,
                    status: project.status,
                    hint: project.project_id
                  }))}
                  onSelect={(id) =>
                    setWorkflowSelection({
                      projectId: id,
                      benchmarkDefinitionId: null,
                      scenarioId: null
                    })
                  }
                  selectedId={selectedProject?.project_id ?? null}
                />
              )}
            </section>
          </aside>

          <div className="project-console__main">
            {!selectedProject ? (
              <section className="project-console__card project-console__card--empty">
                <EmptyState description="先从左侧选择一个项目，再查看该项目的归档结果和运行态。" title="未选择项目" />
              </section>
            ) : workspaceQuery.isLoading ? (
              <section className="project-console__card project-console__card--empty">
                <EmptyState description="正在加载项目工作台接口。" title="项目工作台加载中" />
              </section>
            ) : workspaceQuery.isError || !workspace ? (
              <section className="project-console__card project-console__card--empty">
                <EmptyState
                  description={
                    workspaceQuery.error instanceof Error ? workspaceQuery.error.message : '工作台接口异常。'
                  }
                  title="项目工作台加载失败"
                />
              </section>
            ) : (
              <section className="project-console__card">
                <header className="project-console__card-header">
                  <div>
                    <span className="project-console__section-label">项目只读结果</span>
                    <strong>{workspace.project.name}</strong>
                  </div>
                  <div className="project-console__toggle">
                    <button
                      className={
                        viewMode === 'overview'
                          ? 'project-console__toggle-item project-console__toggle-item--active'
                          : 'project-console__toggle-item'
                      }
                      onClick={() => setViewMode('overview')}
                      type="button"
                    >
                      总览
                    </button>
                    <button
                      className={
                        viewMode === 'reports'
                          ? 'project-console__toggle-item project-console__toggle-item--active'
                          : 'project-console__toggle-item'
                      }
                      onClick={() => setViewMode('reports')}
                      type="button"
                    >
                      报告归档
                    </button>
                    <button
                      className={
                        viewMode === 'runtime'
                          ? 'project-console__toggle-item project-console__toggle-item--active'
                          : 'project-console__toggle-item'
                      }
                      onClick={() => setViewMode('runtime')}
                      type="button"
                    >
                      运行态
                    </button>
                  </div>
                </header>

                {viewMode === 'overview' && (
                  <div className="project-console__section-stack">
                    <div className="project-console__kv-grid">
                      <div className="project-console__kv">
                        <span>厂商 / 平台</span>
                        <strong>{workspace.project.vendor}</strong>
                        <small>{workspace.project.processor}</small>
                      </div>
                      <div className="project-console__kv">
                        <span>适用模板</span>
                        <strong>{workspace.summary.benchmark_definition_count}</strong>
                        <small>只保留摘要，不在这里展开编排。</small>
                      </div>
                      <div className="project-console__kv">
                        <span>归档报告</span>
                        <strong>{reports.length}</strong>
                        <small>{latestReport ? `最新 ${formatDateTime(latestReport.updated_at_utc)}` : '尚无报告'}</small>
                      </div>
                      <div className="project-console__kv">
                        <span>活跃任务</span>
                        <strong>{activeTaskCount}</strong>
                        <small>{workspace.summary.active_run_count} 个运行仍在更新</small>
                      </div>
                    </div>

                    <div className="project-console__chip-block">
                      <div className="project-console__summary-item">
                        <span>项目说明</span>
                        <strong>{workspace.project.name}</strong>
                        <small>{workspace.project.description}</small>
                      </div>
                      <div className="project-console__summary-item">
                        <span>评测关注</span>
                        <div className="project-console__chips">
                          {workspace.project.benchmark_focus.map((item) => (
                            <span className="project-console__chip" key={item}>
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="project-console__summary-item">
                        <span>目标指标</span>
                        <div className="project-console__chips">
                          {workspace.project.target_metrics.map((item) => (
                            <span className="project-console__chip project-console__chip--muted" key={item}>
                              {item}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="project-console__table-split">
                      <div>
                        <div className="project-console__table-title">适用模板摘要</div>
                        <div className="project-console__table">
                          {workspace.benchmark_definitions.map((definition) => (
                            <div className="project-console__table-row" key={definition.benchmark_definition_id}>
                              <div>
                                <span>{definition.name}</span>
                                <strong>{definition.report_shape}</strong>
                                <small>
                                  {planningModeLabel(definition.planning_mode)} / {definition.cadence}
                                </small>
                              </div>
                              <small>{definition.default_project_id ?? workspace.project.project_id}</small>
                              <Link
                                className="horizon-button-secondary"
                                onClick={() =>
                                  setWorkflowSelection({
                                    benchmarkDefinitionId: definition.benchmark_definition_id
                                  })
                                }
                                to="/benchmarks"
                                viewTransition
                              >
                                去编排
                              </Link>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <div className="project-console__table-title">最新归档</div>
                        <div className="project-console__table">
                          {reports.length === 0 ? (
                            <div className="project-console__table-empty">当前项目还没有导出的报告资产。</div>
                          ) : (
                            reports.slice(0, 4).map((report) => (
                              <div className="project-console__table-row" key={report.report_id}>
                                <div>
                                  <span>{report.title}</span>
                                  <strong>{report.benchmark_definition_id}</strong>
                                  <small>{formatDateTime(report.updated_at_utc)}</small>
                                </div>
                                <StatusPill canonical status={report.status} />
                                <div className="project-console__report-actions">
                                  <a
                                    className="horizon-button-secondary"
                                    href={`/reports/${report.report_id}/download?format=json`}
                                    rel="noreferrer"
                                    target="_blank"
                                  >
                                    JSON
                                  </a>
                                </div>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {viewMode === 'reports' && (
                  <div className="project-console__section-stack">
                    <div className="project-console__summary-grid">
                      <div className="project-console__summary-item">
                        <span>报告总数</span>
                        <strong>{reports.length}</strong>
                        <small>按更新时间倒序归档。</small>
                      </div>
                      <div className="project-console__summary-item">
                        <span>待补报告任务</span>
                        <strong>{pendingReportTasks.length}</strong>
                        <small>{archivableTaskCount} 个任务已具备归档条件。</small>
                      </div>
                      <div className="project-console__summary-item">
                        <span>最新报告</span>
                        <strong>{latestReport?.status ?? 'NONE'}</strong>
                        <small>{latestReport ? latestReport.title : '还没有报告资产'}</small>
                      </div>
                      <div className="project-console__summary-item">
                        <span>最近导出时间</span>
                        <strong>{latestReport ? formatDateTime(latestReport.updated_at_utc) : '--'}</strong>
                        <small>报告页负责完整分析，这里只做归档入口。</small>
                      </div>
                    </div>

                    <div className="project-console__table-split">
                      <div>
                        <div className="project-console__table-title">项目报告</div>
                        {reportsQuery.isLoading ? (
                          <EmptyState description="正在同步当前项目的报告资产。" title="报告加载中" />
                        ) : reports.length === 0 ? (
                          <EmptyState description="执行完成并导出后，当前项目的报告会汇总到这里。" title="暂无报告" />
                        ) : (
                          <div className="project-console__table">
                            {reports.map((report) => (
                              <div className="project-console__table-row" key={report.report_id}>
                                <div>
                                  <span>{report.title}</span>
                                  <strong>{report.benchmark_definition_id}</strong>
                                  <small>{formatDateTime(report.updated_at_utc)}</small>
                                </div>
                                <StatusPill canonical status={report.status} />
                                <div className="project-console__report-actions">
                                  <a
                                    className="horizon-button-secondary"
                                    href={`/reports/${report.report_id}/download?format=json`}
                                    rel="noreferrer"
                                    target="_blank"
                                  >
                                    JSON
                                  </a>
                                  <a
                                    className="horizon-button-secondary"
                                    href={`/reports/${report.report_id}/download?format=markdown`}
                                    rel="noreferrer"
                                    target="_blank"
                                  >
                                    MD
                                  </a>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      <div>
                        <div className="project-console__table-title">待补归档</div>
                        <div className="project-console__table">
                          {pendingReportTasks.length === 0 ? (
                            <div className="project-console__table-empty">当前终态任务都已经有报告，或者还没有可归档任务。</div>
                          ) : (
                            pendingReportTasks.map((task) => (
                              <div className="project-console__table-row" key={task.benchmark_task_id}>
                                <div>
                                  <span>{task.benchmark_name}</span>
                                  <strong>{task.status}</strong>
                                  <small>{formatDateTime(task.updated_at_utc)}</small>
                                </div>
                                <small>{task.planned_run_count} runs</small>
                                <Link className="horizon-button-secondary" to="/reports" viewTransition>
                                  去归档
                                </Link>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {viewMode === 'runtime' && (
                  <div className="project-console__section-stack">
                    <div className="project-console__summary-grid">
                      <div className="project-console__summary-item">
                        <span>Executor</span>
                        <strong>{systemQuery.data?.executor.status ?? 'UNKNOWN'}</strong>
                        <small>{systemQuery.data?.executor.warning ?? '无额外警告'}</small>
                      </div>
                      <div className="project-console__summary-item">
                        <span>在线设备</span>
                        <strong>{workspace.summary.online_gateway_count}</strong>
                        <small>总计 {workspace.summary.total_gateway_count}</small>
                      </div>
                      <div className="project-console__summary-item">
                        <span>最近运行</span>
                        <strong>{workspace.summary.recent_run_count}</strong>
                        <small>{latestRun ? latestRun.scenario_name : '暂无运行'}</small>
                      </div>
                      <div className="project-console__summary-item">
                        <span>最近任务</span>
                        <strong>{workspace.summary.benchmark_task_count}</strong>
                        <small>{latestTask ? latestTask.benchmark_name : '暂无任务'}</small>
                      </div>
                    </div>

                    <div className="project-console__table-split">
                      <div>
                        <div className="project-console__table-title">最近运行</div>
                        <div className="project-console__table">
                          {workspace.recent_runs.length === 0 ? (
                            <div className="project-console__table-empty">当前项目暂无运行记录。</div>
                          ) : (
                            workspace.recent_runs.slice(0, 6).map((run) => (
                              <div className="project-console__table-row" key={run.run_id}>
                                <div>
                                  <span>{run.scenario_name}</span>
                                  <strong>{run.status}</strong>
                                  <small>{truncateMiddle(run.run_id, 18)}</small>
                                </div>
                                <small>{run.execution_backend}</small>
                                <Link className="horizon-button-secondary" to="/executions" viewTransition>
                                  去查看
                                </Link>
                              </div>
                            ))
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="project-console__table-title">设备状态</div>
                        <div className="project-console__table">
                          {workspace.gateways.length === 0 ? (
                            <div className="project-console__table-empty">当前没有设备状态。</div>
                          ) : (
                            workspace.gateways.map((gateway) => (
                              <div className="project-console__table-row" key={gateway.gateway_id}>
                                <div>
                                  <span>{gateway.name}</span>
                                  <strong>{gateway.status}</strong>
                                  <small>{gateway.address ?? gateway.gateway_id}</small>
                                </div>
                                <small>{gateway.current_run_id ? 'BUSY' : 'IDLE'}</small>
                                <Link className="horizon-button-secondary" to="/devices" viewTransition>
                                  去设备页
                                </Link>
                              </div>
                            ))
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </section>
            )}
          </div>

          <aside className="project-console__summary">
            <section className="project-console__card">
              <header className="project-console__card-header">
                <div>
                  <span className="project-console__section-label">当前项目</span>
                  <strong>项目定位</strong>
                </div>
              </header>

              {workspace ? (
                <div className="project-console__summary-stack">
                  <p>项目: {workspace.project.name}</p>
                  <p>厂商: {workspace.project.vendor}</p>
                  <p>平台: {workspace.project.processor}</p>
                  <small>项目页只看归档与运行态，不再在这里展开模板和场景配置细节。</small>
                </div>
              ) : (
                <EmptyState description="选择项目后显示项目定位。" title="没有项目定位" />
              )}
            </section>

            <section className="project-console__card">
              <header className="project-console__card-header">
                <div>
                  <span className="project-console__section-label">快速跳转</span>
                  <strong>下一步入口</strong>
                </div>
              </header>

              <div className="project-console__action-grid">
                <Link className="horizon-button project-console__action-link" to="/benchmarks" viewTransition>
                  基准任务
                </Link>
                <Link className="horizon-button-secondary project-console__action-link" to="/reports" viewTransition>
                  报告中心
                </Link>
                <Link className="horizon-button-secondary project-console__action-link" to="/executions" viewTransition>
                  执行中心
                </Link>
                <Link className="horizon-button-secondary project-console__action-link" to="/scenario-sets" viewTransition>
                  场景集
                </Link>
              </div>
            </section>

            <section className="project-console__card">
              <header className="project-console__card-header">
                <div>
                  <span className="project-console__section-label">最近归档</span>
                  <strong>最新资产</strong>
                </div>
              </header>

              {latestReport ? (
                <div className="project-console__summary-stack">
                  <p>报告: {latestReport.title}</p>
                  <p>状态: {latestReport.status}</p>
                  <p>时间: {formatDateTime(latestReport.updated_at_utc)}</p>
                  <div className="project-console__report-actions">
                    <a
                      className="horizon-button-secondary"
                      href={`/reports/${latestReport.report_id}/download?format=json`}
                      rel="noreferrer"
                      target="_blank"
                    >
                      JSON
                    </a>
                    <a
                      className="horizon-button-secondary"
                      href={`/reports/${latestReport.report_id}/download?format=markdown`}
                      rel="noreferrer"
                      target="_blank"
                    >
                      Markdown
                    </a>
                  </div>
                </div>
              ) : latestTask ? (
                <div className="project-console__summary-stack">
                  <p>最近任务: {latestTask.benchmark_name}</p>
                  <p>状态: {latestTask.status}</p>
                  <p>时间: {formatDateTime(latestTask.updated_at_utc)}</p>
                  <small>当前还没有导出报告，可以到报告中心继续归档。</small>
                </div>
              ) : (
                <EmptyState description="当前项目还没有任务或报告资产。" title="没有归档内容" />
              )}
            </section>
          </aside>
        </div>
      </section>
    </div>
  );
}
