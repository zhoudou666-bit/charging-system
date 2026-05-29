<template>
  <div>
    <div class="page-header">
      <div>
        <h2>充电桩状态监测</h2>
        <p>查看校园充电桩实时状态，支持空闲充电桩预约与实时数据采集。</p>
      </div>

      <el-button type="primary" @click="loadPileList">
        刷新充电桩
      </el-button>
    </div>

    <el-table :data="pileList" border style="width: 100%;">
      <el-table-column prop="pile_name" label="充电桩名称" min-width="160" />

      <el-table-column prop="location" label="位置" min-width="180" />

      <el-table-column label="状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.status === '空闲'" type="success">空闲</el-tag>
          <el-tag v-else-if="scope.row.status === '占用'" type="warning">占用</el-tag>
          <el-tag v-else-if="scope.row.status === '故障'" type="danger">故障</el-tag>
          <el-tag v-else>{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="更新时间" min-width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.update_time) }}
        </template>
      </el-table-column>

      <el-table-column label="操作" width="280">
        <template #default="scope">
          <el-button
            type="primary"
            @click="simulate(scope.row)"
            :disabled="scope.row.status === '故障'"
          >
            查看实时数据
          </el-button>

          <el-button
            type="success"
            @click="reserve(scope.row)"
            :disabled="scope.row.status !== '空闲'"
          >
            预约
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-card v-if="currentData" class="data-card">
      <template #header>
        <div class="card-header">
          <span>实时充电数据</span>
          <el-tag
            :type="currentData.warning_status === '正常' ? 'success' : 'warning'"
          >
            {{ currentData.warning_status }}
          </el-tag>
        </div>
      </template>

      <div class="data-grid">
        <div class="data-item">
          <span class="label">充电桩编号</span>
          <span class="value">{{ currentData.pile_id }}</span>
        </div>

        <div class="data-item">
          <span class="label">电压</span>
          <span class="value">{{ currentData.voltage }} V</span>
        </div>

        <div class="data-item">
          <span class="label">电流</span>
          <span class="value">{{ currentData.current_value }} A</span>
        </div>

        <div class="data-item">
          <span class="label">功率</span>
          <span class="value">{{ currentData.power }} kW</span>
        </div>

        <div class="data-item">
          <span class="label">采集时间</span>
          <span class="value time-value">
            {{ formatDateTime(currentData.create_time) }}
          </span>
        </div>
      </div>

      <el-alert
        v-if="currentData.warning_status !== '正常'"
        :title="currentData.warning_status"
        description="检测到充电风险，系统已自动生成安全预警记录。"
        type="warning"
        show-icon
        style="margin-top: 16px;"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../api'
import { ElMessage } from 'element-plus'
import { formatDateTime } from '../utils/time'

const pileList = ref([])
const currentData = ref(null)

let timer = null

const loadPileList = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/pile/list`)
    pileList.value = res.data.data || []
  } catch (error) {
    console.error('获取充电桩列表失败：', error)
    ElMessage.error('获取充电桩列表失败，请检查后端是否运行')
  }
}

const simulate = async (row) => {
  if (row.status === '故障') {
    ElMessage.warning('故障充电桩不可采集实时数据')
    return
  }

  try {
    const res = await axios.get(`${API_BASE_URL}/api/pile/simulate/${row.id}`)

    currentData.value = res.data.data

    ElMessage.success('实时数据获取成功')

    if (currentData.value.warning_status !== '正常') {
      ElMessage.warning('检测到过载风险，已生成预警记录')
    }

    await loadPileList()
  } catch (error) {
    console.error('获取实时数据失败：', error)
    ElMessage.error('获取实时数据失败，请检查后端接口')
  }
}

const reserve = async (row) => {
  if (row.status !== '空闲') {
    ElMessage.warning('只有空闲充电桩可以预约')
    return
  }

  try {
    const res = await axios.post(`${API_BASE_URL}/api/reservation/add`, {
      user_id: 1,
      pile_id: row.id
    })

    if (res.data.code === 200) {
      ElMessage.success(
        res.data.message || '预约成功，预约有效期为 5 分钟，到期后系统将自动确认充电并生成充电记录'
      )
    } else {
      ElMessage.error(res.data.message || '预约失败')
    }

    await loadPileList()
  } catch (error) {
    console.error('预约失败：', error)

    const message = error.response?.data?.message || '预约失败，请检查后端接口'
    ElMessage.error(message)
  }
}

onMounted(() => {
  loadPileList()

  timer = setInterval(() => {
    loadPileList()
  }, 10000)
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  color: #0f172a;
}

.page-header p {
  margin: 8px 0 0;
  color: #64748b;
  font-size: 14px;
}

.data-card {
  margin-top: 22px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 700;
  color: #0f172a;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(120px, 1fr));
  gap: 14px;
}

.data-item {
  padding: 16px;
  border-radius: 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.label {
  display: block;
  margin-bottom: 8px;
  font-size: 13px;
  color: #64748b;
}

.value {
  font-size: 20px;
  font-weight: 800;
  color: #2563eb;
}

.time-value {
  font-size: 15px;
}

@media (max-width: 1100px) {
  .data-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .data-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>