<template>
  <div>
    <h2>充电桩状态监测</h2>

    <el-table :data="pileList" border style="width: 100%;">
      <el-table-column prop="pile_name" label="充电桩名称" />
      <el-table-column prop="location" label="位置" />

      <el-table-column label="状态">
        <template #default="scope">
          <el-tag v-if="scope.row.status === '空闲'" type="success">空闲</el-tag>
          <el-tag v-else-if="scope.row.status === '占用'" type="warning">占用</el-tag>
          <el-tag v-else-if="scope.row.status === '故障'" type="danger">故障</el-tag>
          <el-tag v-else>{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="260">
        <template #default="scope">
          <el-button type="primary" @click="simulate(scope.row)">
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

    <el-card v-if="currentData" style="margin-top: 20px;">
      <h3>实时充电数据</h3>
      <p>充电桩编号：{{ currentData.pile_id }}</p>
      <p>电压：{{ currentData.voltage }} V</p>
      <p>电流：{{ currentData.current_value }} A</p>
      <p>功率：{{ currentData.power }} kW</p>
      <p>状态判断：{{ currentData.warning_status }}</p>

      <el-alert
        v-if="currentData.warning_status !== '正常'"
        :title="currentData.warning_status"
        type="warning"
        show-icon
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../api'
import { ElMessage } from 'element-plus'

const pileList = ref([])
const currentData = ref(null)

const loadPileList = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/pile/list`)
    pileList.value = res.data.data
  } catch (error) {
    console.error('获取充电桩列表失败：', error)
    ElMessage.error('获取充电桩列表失败，请检查后端是否运行')
  }
}

const simulate = async (row) => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/pile/simulate/${row.id}`)

    currentData.value = res.data.data

    ElMessage.success('实时数据获取成功')

    if (currentData.value.warning_status !== '正常') {
      ElMessage.warning('检测到过载风险，已生成预警记录')
    }
  } catch (error) {
    console.error('获取实时数据失败：', error)
    ElMessage.error('获取实时数据失败，请检查后端接口')
  }
}

const reserve = async (row) => {
  try {
    await axios.post(`${API_BASE_URL}/api/reservation/add`, {
      user_id: 1,
      pile_id: row.id,
      start_time: '2026-05-14 10:00:00',
      end_time: '2026-05-14 12:00:00'
    })

    ElMessage.success('预约成功')
  } catch (error) {
    console.error('预约失败：', error)
    ElMessage.error('预约失败，请检查后端接口')
  }
}

onMounted(() => {
  loadPileList()
})
</script>