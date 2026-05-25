<template>
  <div>
    <h2>安全预警记录</h2>

    <el-alert
      v-if="props.userRole !== 'admin'"
      title="当前为学生账号，仅可查看预警记录，不能处理或删除预警"
      type="info"
      show-icon
      style="margin-bottom: 15px;"
    />

    <el-button type="primary" @click="loadWarnings">
      刷新预警记录
    </el-button>

    <el-table :data="warningList" border style="width: 100%; margin-top: 20px;">
      <el-table-column prop="warning_type" label="预警类型" width="160" />

      <el-table-column label="预警等级" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.warning_level === '严重'" type="danger">
            严重
          </el-tag>
          <el-tag v-else type="warning">
            {{ scope.row.warning_level || '一般' }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="风险说明" min-width="300">
        <template #default="scope">
          {{ getReasonText(scope.row.description) }}
        </template>
      </el-table-column>

      <el-table-column label="处置建议" min-width="300">
        <template #default="scope">
          {{ getSuggestionText(scope.row.description, scope.row.warning_type) }}
        </template>
      </el-table-column>

      <el-table-column label="处理状态" width="120">
        <template #default="scope">
          <el-tag v-if="scope.row.status === '已处理'" type="success">
            已处理
          </el-tag>
          <el-tag v-else type="danger">
            未处理
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="时间" min-width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.create_time) }}
        </template>
      </el-table-column>

      <el-table-column
        v-if="props.userRole === 'admin'"
        label="操作"
        width="180"
        fixed="right"
      >
        <template #default="scope">
          <el-button
            type="success"
            size="small"
            @click="handleWarning(scope.row)"
            :disabled="scope.row.status === '已处理'"
          >
            处理
          </el-button>

          <el-button
            type="danger"
            size="small"
            @click="deleteWarning(scope.row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '../utils/time'

const props = defineProps({
  userRole: {
    type: String,
    default: 'student'
  }
})

const warningList = ref([])

const loadWarnings = async () => {
  try {
    const res = await axios.get(`${API_BASE_URL}/api/warning/list`)
    warningList.value = res.data.data
  } catch (error) {
    console.error('获取预警记录失败：', error)
    ElMessage.error('获取预警记录失败，请检查后端接口')
  }
}

const getReasonText = (description) => {
  if (!description) {
    return '暂无风险说明'
  }

  if (description.includes('处置建议：')) {
    return description.split('处置建议：')[0]
  }

  return description
}

const getSuggestionText = (description, warningType) => {
  if (description && description.includes('处置建议：')) {
    return description.split('处置建议：')[1]
  }

  if (warningType === '过载充电') {
    return '建议立即检查充电设备，提醒用户停止高功率充电，必要时暂停该充电桩使用。'
  }

  if (warningType === '电动车进宿舍') {
    return '建议通知宿管或管理员现场巡查，要求车辆移出室内区域，并记录违规行为。'
  }

  if (warningType === '私拉电线') {
    return '建议立即切断违规线路，检查线路绝缘情况，并提醒用户使用规范充电设施。'
  }

  if (warningType === '插座过载') {
    return '建议减少接入设备数量，检查插座负载能力，必要时暂停使用该插座。'
  }

  return '建议管理员及时核查并处理。'
}

const handleWarning = async (row) => {
  if (props.userRole !== 'admin') {
    ElMessage.warning('学生账号不能处理预警')
    return
  }

  try {
    const res = await axios.post(`${API_BASE_URL}/api/warning/handle/${row.id}`)

    if (res.data.code === 200) {
      ElMessage.success(res.data.message || '处理成功')
      await loadWarnings()
    } else {
      ElMessage.error(res.data.message || '处理失败')
    }
  } catch (error) {
    console.error('处理预警失败：', error)
    ElMessage.error('处理失败，请检查后端接口')
  }
}

const deleteWarning = async (row) => {
  if (props.userRole !== 'admin') {
    ElMessage.warning('只有管理员可以删除预警记录')
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定要删除这条 ${row.warning_type} 预警记录吗？`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const res = await axios.delete(`${API_BASE_URL}/api/warning/delete/${row.id}`, {
      data: {
        role: props.userRole
      }
    })

    if (res.data.code === 200) {
      ElMessage.success(res.data.message || '预警记录删除成功')
      await loadWarnings()
    } else {
      ElMessage.error(res.data.message || '预警记录删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除预警记录失败：', error)
      ElMessage.error('删除预警记录失败，请检查后端接口')
    }
  }
}

onMounted(() => {
  loadWarnings()
})
</script>