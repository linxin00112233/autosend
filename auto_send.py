import requests
import json
from datetime import datetime, timedelta

def fetch_and_send():
    # 1. 配置信息
    # 接口地址（来自你的文档）
    data_url = "https://str.aimirainnovation.com/api/public/dashboard"
    # 企微 Webhook（建议重置后再替换此处）
    wechat_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9167b647-def5-48db-abf5-466f91a9ad55"
    
    try:
        # 2. 获取接口数据
        response = requests.get(data_url, timeout=15)
        if response.status_code != 200:
            print(f"接口请求失败，状态码: {response.status_code}")
            return
        
        res_json = response.json()
        if res_json.get("code") != 0:
            print(f"业务报错: {res_json.get('message')}")
            return
            
        data = res_json.get("data", {})
        
        # 3. 解析汇总字段 (对应文档 5.1)
        total_sub = data.get("total_submissions", 0)
        today_sub = data.get("submissions_today", 0)
        avg_score = data.get("average_score") or 0
        pass_cnt = data.get("pass_count", 0)
        fail_cnt = data.get("fail_count", 0)
        pass_rate = data.get("pass_rate") or 0
        avg_time = data.get("avg_time_to_complete_minutes") or 0

        # 4. 解析状态分布 (对应文档 5.2)
        status_map = {
            "failed": "未通过",
            "completed": "已完成",
            "transcribing": "转录中",
            "submitted": "已提交",
            "scoring": "评分中"
        }
        status_data = data.get("status_distribution", {})
        status_lines = []
        for key, count in status_data.items():
            cn_name = status_map.get(key, key)
            percent = (count / total_sub * 100) if total_sub > 0 else 0
            status_lines.append(f"{cn_name}: {count} 人 ({percent:.1f}%)")
        status_str = "\n".join(status_lines)

        # 5. 解析热门岗位TOP5 (对应文档 5.3)
        job_list = data.get("job_distribution", [])
        # 按人数倒序排列并取前5
        job_list = sorted(job_list, key=lambda x: x['count'], reverse=True)[:5]
        job_lines = []
        for job in job_list:
            percent = (job['count'] / total_sub * 100) if total_sub > 0 else 0
            job_lines.append(f"{job['name']}: {job['count']} 人 ({percent:.1f}%)")
        job_str = "\n".join(job_lines)

        # 6. 解析七日趋势 (对应文档 5.5)
        trend_list = data.get("daily_trend", [])
        trend_lines = []
        trend_total = sum(t['count'] for t in trend_list)
        for t in trend_list:
            trend_lines.append(f"{t['date']}: {t['count']} 人")
        trend_str = "\n".join(trend_lines)

        # 7. 解析评分分布 (对应文档 5.6)
        score_buckets = data.get("score_buckets", [])
        score_total = sum(item['count'] for item in score_buckets)
        score_lines = []
        for b in score_buckets:
            percent = (b['count'] / score_total * 100) if score_total > 0 else 0
            score_lines.append(f"{b['label']}分: {b['count']} 人 ({percent:.1f}%)")
        score_str = "\n".join(score_lines)

        # 8. 组装 Markdown 消息
        # 重点：修正 GitHub Actions 的 8 小时时差
        # utcnow 获取标准时间，timedelta(hours=8) 补偿到北京/香港时间
        bj_time = datetime.utcnow() + timedelta(hours=8)
        now_str = bj_time.strftime('%Y-%m-%d %H:%M')

        report_content = (
            f"📊 **招聘看板数据分析报告**\n"
            f"生成时间: {now_str}\n"
            f"数据来源: [aimirainnovation.com](https://str.aimirainnovation.com)\n\n"
            f"【**关键指标**】\n"
            f"总提交数: {total_sub} 人\n"
            f"今日提交: <font color=\"warning\">{today_sub} 人</font>\n"
            f"全局平均分: {avg_score:.1f} 分\n"
            f"通过人数: {pass_cnt} 人\n"
            f"未通过人数: {fail_cnt} 人\n"
            f"全局通过率: <font color=\"info\">{pass_rate}%</font>\n"
            f"平均处理时长: {avg_time:.1f} 分钟\n\n"
            f"【**状态分布**】\n{status_str}\n\n"
            f"【**热门岗位TOP5**】\n{job_str}\n\n"
            f"【**七日提交趋势**】\n{trend_str}\n"
            f"七日总计: {trend_total} 人\n\n"
            f"【**评分分布**】\n{score_str}"
        )

        # 9. 推送到企微
        payload = {
            "msgtype": "markdown",
            "markdown": {"content": report_content}
        }
        headers = {'Content-Type': 'application/json'}
        requests.post(wechat_url, data=json.dumps(payload), headers=headers)
        print(f"[{now_str}] 推送任务完成。")

    except Exception as e:
        print(f"程序运行出错: {e}")

if __name__ == "__main__":
    fetch_and_send()