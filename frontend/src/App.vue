<template>
  <Login v-if="!isLogin" @login-success="handleLoginSuccess" />

  <div v-else class="main-page">
    <div class="top-bar">
      <h1>校园电动车充电监测 + AI安全预警系统</h1>

      <div>
        <span class="user-info">
          当前用户：{{ currentUser.username }}（{{ currentUser.role }}）
        </span>
        <el-button type="danger" @click="logout">退出登录</el-button>
      </div>
    </div>

    <el-row :gutter="20" style="margin-bottom: 25px;">
      <el-col :span="4">
        <el-card>
          <h3>充电桩总数</h3>
          <p class="num">{{ stats.total }}</p>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card>
          <h3>空闲数量</h3>
          <p class="num">{{ stats.free_count }}</p>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card>
          <h3>占用数量</h3>
          <p class="num">{{ stats.used_count }}</p>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card>
          <h3>故障数量</h3>
          <p class="num">{{ stats.fault_count }}</p>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card>
          <h3>预警数量</h3>
          <p class="num">{{ stats.warning_count }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-tabs v-model="activeTab" @tab-change="loadStats">
      <el-tab-pane label="充电桩监测" name="pile">
        <PileList />
      </el-tab-pane>

      <el-tab-pane label="充电数据记录" name="data">
        <ChargingData />
      </el-tab-pane>

      <el-tab-pane label="安全预警记录" name="warning">
        <WarningList :user-role="currentUser.role" />
      </el-tab-pane>

      <el-tab-pane label="AI模拟识别" name="ai">
        <AiMock />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from './api'

import Login from './components/Login.vue'
import PileList from './components/PileList.vue'
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
.main-page {
  padding: 30px;
  background: #f5f7fa;
  min-height: 100vh;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.user-info {
  margin-right: 15px;
  color: #666;
}

.num {
  font-size: 30px;
  font-weight: bold;
  color: #409eff;
}
</style>