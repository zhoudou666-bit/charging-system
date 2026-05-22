<template>
  <div>
    <div class="page-header">
      <div>
        <h2>预约记录</h2>
        <p>学生预约充电后，系统将在 5 分钟后自动确认充电，并生成一条正常充电记录。</p>
      </div>

      <el-button type="primary" @click="loadReservations">
        刷新预约记录
      </el-button>
    </div>

    <el-table :data="reservationList" border style="width: 100%; margin-top: 18px;">
      <el-table-column prop="pile_name" label="充电桩" width="160" />
      <el-table-column prop="location" label="位置" width="180" />

      <el-table-column label="预约开始时间" min-width="190">
        <template #default="scope">
          {{ formatDateTime(scope.row.start_time) }}
        </template>
      </el-table-column>

      <el-table-column label="预约结束时间" min-width="190">
        <template #default="scope">
          {{ formatDateTime(scope.row.end_time) }}
        </template>
      </el-table-column>

      <el-table-column label="创建时间" min-width="190">
        <template #default="scope">
          {{ formatDateTime(scope.row.create_time) }}
        </template>
      </el-table-column>

      <el-table-column label="预约状态" width="130">
        <template #default="scope">
          <el-tag v-if="scope.row.status === '已预约'" type="success">
            已预约
          </el-tag>

          <el-tag v-else-if="scope.row.status === '已取消'" type="info">
            已取消
          </el-tag>

          <el-tag v-else-if="scope.row.status === '已充电'" type="primary">
            已充电
          </el-tag>

          <el-tag v-else type="warning">
            {{ scope.row.status }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { API_BASE_URL } from '../api'
import { formatDateTime } from '../utils/time'

const reservationList = ref([])

const loadReservations = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/reservation/list`)
    reservationList.value = res.data.data
  } catch (error) {
    console.error(error)
    ElMessage.error('预约记录获取失败，请检查后端接口')
  }
}

onMounted(() => {
  loadReservations()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
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
</style>