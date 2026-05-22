<template>
  <Login v-if="!isLogin" @login-success="handleLoginSuccess" />

  <div v-else class="app-container">
    <!-- 顶部标题栏 -->
    <div class="top-bar">
      <div class="title-block">
        <h1>校园电动车充电安全智能体平台</h1>
        <div class="top-subtitle">
          面向校园场景的充电监测、风险识别、预警生成与闭环处置系统
        </div>
      </div>

      <div class="user-info">
        <span>当前用户：{{ currentUser.username }}（{{ currentUser.role }}）</span>
        <span class="role-badge">
          {{ currentUser.role === 'admin' ? '管理员端' : '学生端' }}
        </span>
        <el-button type="danger" @click="logout">退出登录</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-blue">
        <div class="stat-icon">⚡</div>
        <div class="stat-title">充电桩总数</div>
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-desc">当前系统纳管设备数量</div>
      </div>

      <div class="stat-card stat-green">
        <div class="stat-icon">✅</div>
        <div class="stat-title">空闲数量</div>
        <div class="stat-value">{{ stats.free_count }}</div>
        <div class="stat-desc">当前可预约充电桩数量</div>
      </div>

      <div class="stat-card stat-orange">
        <div class="stat-icon">🔌</div>
        <div class="stat-title">占用数量</div>
        <div class="stat-value">{{ stats.used_count }}</div>
        <div class="stat-desc">正在使用中的充电设备</div>
      </div>

      <div class="stat-card stat-red">
        <div class="stat-icon">🛠️</div>
        <div class="stat-title">故障数量</div>
        <div class="stat-value">{{ stats.fault_count }}</div>
        <div class="stat-desc">需要检修维护的设备</div>
      </div>

      <div class="stat-card stat-purple">
        <div class="stat-icon">🚨</div>
        <div class="stat-title">预警数量</div>
        <div class="stat-value">{{ stats.warning_count }}</div>
        <div class="stat-desc">当前累计安全风险记录</div>
      </div>
    </div>

    <!-- 系统状态条 -->
    <div class="status-strip">
      <div>
        <span class="status-dot"></span>
        系统状态：运行中
      </div>
      <div>数据来源：Railway MySQL 云数据库</div>
      <div>智能体流程：场景感知 → 风险识别 → 等级判断 → 预警处置</div>
      <div>预约机制：5 分钟未充电自动取消</div>
    </div>

    <!-- 主功能面板 -->
    <div class="main-panel">
      <el-tabs v-model="activeTab" @tab-change="loadStats">
        <el-tab-pane label="充电桩监测" name="pile">
          <PileList />
        </el-tab-pane>

        <el-tab-pane label="预约记录" name="reservation">
          <ReservationList />
        </el-tab-pane>

        <el-tab-pane label="充电数据记录" name="data">
          <ChargingData />
        </el-tab-pane>

        <el-tab-pane label="安全预警记录" name="warning">
          <WarningList :user-role="currentUser.role" />
        </el-tab-pane>

        <el-tab-pane label="AI安全巡检智能体" name="ai">
          <AiMock />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from './api'

import Login from './components/Login.vue'
import PileList from './components/PileList.vue'
import ReservationList from './components/ReservationList.vue'
import ChargingData from './components/ChargingData.vue'
import WarningList from './components/WarningList.vue'
import AiMock from './components/AiMock.vue'

const isLogin = ref(false)
const currentUser = ref({})
const activeTab = ref('pile')

const stats = ref({
  total: 0,
  free_count: 0,
  used_count: 0,
  fault_count: 0,
  warning_count: 0
})

const loadStats = async () => {
  const res = await axios.get(`${API_BASE_URL}/api/stats`)
  stats.value = res.data.data
}

const handleLoginSuccess = (user) => {
  currentUser.value = user
  isLogin.value = true
  activeTab.value = 'pile'
  loadStats()
}

const logout = () => {
  isLogin.value = false
  currentUser.value = {}
  activeTab.value = 'pile'
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  padding: 28px 36px;
  background:
    radial-gradient(circle at top left, rgba(64, 158, 255, 0.16), transparent 28%),
    radial-gradient(circle at top right, rgba(139, 92, 246, 0.12), transparent 30%),
    linear-gradient(135deg, #f4f7fb 0%, #eef3f8 100%);
  color: #1f2937;
  box-sizing: border-box;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px 28px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
  border-radius: 22px;
  box-shadow: 0 14px 35px rgba(15, 23, 42, 0.09);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

.title-block h1 {
  margin: 0;
  font-size: 31px;
  font-weight: 850;
  letter-spacing: 0.4px;
  color: #0f172a;
}

.top-subtitle {
  margin-top: 9px;
  font-size: 14px;
  color: #64748b;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 14px;
  font-size: 14px;
  color: #475569;
}

.role-badge {
  padding: 6px 13px;
  border-radius: 999px;
  background: linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%);
  color: #0369a1;
  font-weight: 700;
  border: 1px solid rgba(14, 165, 233, 0.22);
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(155px, 1fr));
  gap: 18px;
  margin-bottom: 18px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  min-height: 136px;
  padding: 22px 20px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 20px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.96);
  transition: all 0.25s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.13);
}

.stat-card::after {
  content: "";
  position: absolute;
  right: -34px;
  top: -34px;
  width: 104px;
  height: 104px;
  border-radius: 50%;
  opacity: 0.16;
}

.stat-blue::after {
  background: #2563eb;
}

.stat-green::after {
  background: #16a34a;
}

.stat-orange::after {
  background: #f59e0b;
}

.stat-red::after {
  background: #dc2626;
}

.stat-purple::after {
  background: #7c3aed;
}

.stat-icon {
  position: absolute;
  right: 18px;
  top: 18px;
  font-size: 24px;
  z-index: 1;
}

.stat-title {
  font-size: 15px;
  font-weight: 750;
  color: #334155;
  margin-bottom: 16px;
}

.stat-value {
  font-size: 36px;
  line-height: 1;
  font-weight: 850;
  margin-bottom: 12px;
}

.stat-blue .stat-value {
  color: #2563eb;
}

.stat-green .stat-value {
  color: #16a34a;
}

.stat-orange .stat-value {
  color: #f59e0b;
}

.stat-red .stat-value {
  color: #dc2626;
}

.stat-purple .stat-value {
  color: #7c3aed;
}

.stat-desc {
  font-size: 12px;
  color: #94a3b8;
}

.status-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  align-items: center;
  margin-bottom: 22px;
  padding: 14px 18px;
  background: rgba(15, 23, 42, 0.82);
  color: #e5e7eb;
  border-radius: 16px;
  font-size: 13px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.16);
}

.status-dot {
  display: inline-block;
  width: 9px;
  height: 9px;
  margin-right: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.2);
}

.main-panel {
  padding: 24px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
  border-radius: 22px;
  box-shadow: 0 14px 36px rgba(15, 23, 42, 0.09);
  border: 1px solid rgba(226, 232, 240, 0.95);
}

:deep(.el-tabs__header) {
  margin-bottom: 24px;
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #dbe4ef;
}

:deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 700;
  color: #475569;
}

:deep(.el-tabs__item.is-active) {
  color: #2563eb;
}

:deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 999px;
  background-color: #2563eb;
}

:deep(.el-table) {
  border-radius: 16px;
  overflow: hidden;
  color: #334155;
}

:deep(.el-table th.el-table__cell) {
  background: #f8fafc;
  color: #475569;
  font-weight: 750;
}

:deep(.el-table td.el-table__cell) {
  padding: 13px 0;
}

:deep(.el-button) {
  border-radius: 10px;
  font-weight: 700;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #409eff 0%, #2563eb 100%);
  border: none;
}

:deep(.el-button--success) {
  background: linear-gradient(135deg, #67c23a 0%, #16a34a 100%);
  border: none;
}

:deep(.el-button--danger) {
  background: linear-gradient(135deg, #f56c6c 0%, #dc2626 100%);
  border: none;
}

:deep(.el-card) {
  border-radius: 18px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
}

:deep(.el-alert) {
  border-radius: 12px;
}

@media (max-width: 1200px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .top-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}

@media (max-width: 720px) {
  .app-container {
    padding: 18px;
  }

  .stats-row {
    grid-template-columns: 1fr;
  }

  .user-info {
    flex-wrap: wrap;
  }

  .title-block h1 {
    font-size: 24px;
  }
}
</style>