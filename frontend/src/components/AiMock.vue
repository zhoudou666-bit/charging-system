<template>
  <div>
    <h2>AI安全巡检智能体</h2>

    <el-alert
      title="当前版本采用AI模拟识别方式，模拟智能体对校园充电安全场景进行风险分析、等级判断和预警生成。后续可接入YOLOv8实现真实图片识别。"
      type="info"
      show-icon
      style="margin-bottom: 20px;"
    />

    <el-card style="margin-bottom: 20px;">
      <h3>一、选择巡检场景</h3>

      <el-radio-group v-model="scene">
        <el-radio-button label="宿舍楼道" />
        <el-radio-button label="充电区域" />
        <el-radio-button label="教学楼入口" />
        <el-radio-button label="食堂周边" />
      </el-radio-group>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <h3>二、选择风险类型</h3>

      <el-radio-group v-model="warningType">
        <el-radio-button label="电动车进宿舍" />
        <el-radio-button label="私拉电线" />
        <el-radio-button label="插座过载" />
      </el-radio-group>
    </el-card>

    <el-card style="margin-bottom: 20px;">
      <h3>三、AI智能体分析</h3>

      <el-button type="danger" @click="startAnalyze">
        开始智能分析
      </el-button>

      <el-steps
        v-if="analyzed"
        :active="4"
        finish-status="success"
        style="margin-top: 25px;"
      >
        <el-step title="场景感知" />
        <el-step title="风险识别" />
        <el-step title="等级判断" />
        <el-step title="生成预警" />
      </el-steps>
    </el-card>

    <el-card v-if="result" style="margin-top: 20px;">
      <h3>四、智能体分析结果</h3>

      <el-descriptions border :column="1">
        <el-descriptions-item label="巡检场景">
          {{ result.scene }}
        </el-descriptions-item>

        <el-descriptions-item label="识别风险">
          {{ result.warning_type }}
        </el-descriptions-item>

        <el-descriptions-item label="风险等级">
          <el-tag :type="result.warning_level === '严重' ? 'danger' : 'warning'">
            {{ result.warning_level }}
          </el-tag>
        </el-descriptions-item>

        <el-descriptions-item label="风险原因">
          {{ result.reason }}
        </el-descriptions-item>

        <el-descriptions-item label="处置建议">
          {{ result.suggestion }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { API_BASE_URL } from '../api'
import { ElMessage } from 'element-plus'

const scene = ref('宿舍楼道')
const warningType = ref('电动车进宿舍')
const analyzed = ref(false)
const result = ref(null)

const getReason = (type, sceneName) => {
  if (type === '电动车进宿舍') {
    return `${sceneName}中发现电动车进入室内区域，存在违规停放、违规充电和消防通道堵塞风险。`
  }

  if (type === '私拉电线') {
    return `${sceneName}中存在非规范线路连接，可能造成线路短路、漏电或过载风险。`
  }

  if (type === '插座过载') {
    return `${sceneName}中检测到多设备同时接入插座，存在负载过高和发热风险。`
  }

  return '检测到异常安全风险。'
}

const getSuggestion = (type) => {
  if (type === '电动车进宿舍') {
    return '建议通知宿管或管理员现场巡查，要求车辆移出室内区域，并对违规行为进行记录。'
  }

  if (type === '私拉电线') {
    return '建议立即切断违规线路，检查线路绝缘情况，并提醒用户使用规范充电设施。'
  }

  if (type === '插座过载') {
    return '建议减少接入设备数量，检查插座负载能力，必要时暂停使用该插座。'
  }

  return '建议管理员及时核查并处理。'
}

const getLevel = (type) => {
  if (type === '电动车进宿舍') {
    return '严重'
  }

  if (type === '插座过载') {
    return '严重'
  }

  return '一般'
}

const startAnalyze = async () => {
  analyzed.value = false
  result.value = null

  const level = getLevel(warningType.value)
  const reason = getReason(warningType.value, scene.value)
  const suggestion = getSuggestion(warningType.value)

  // 先显示智能体分析结果，避免后端接口异常时页面无反应
  result.value = {
    scene: scene.value,
    warning_type: warningType.value,
    warning_level: level,
    reason: reason,
    suggestion: suggestion
  }

  analyzed.value = true

  try {
    await axios.post(`${API_BASE_URL}/api/ai/mock-detect`, {
      warning_type: warningType.value,
      warning_level: level,
      description: reason,
      suggestion: suggestion
    })

    ElMessage.success('AI智能体分析完成，已生成安全预警记录')
  } catch (error) {
    console.error('AI智能体分析写入预警失败：', error)
    ElMessage.warning('前端已完成分析，但写入预警记录失败，请检查后端接口')
  }
}
</script>