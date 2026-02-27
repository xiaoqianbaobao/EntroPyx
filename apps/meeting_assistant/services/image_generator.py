import os
import logging
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from django.conf import settings

logger = logging.getLogger(__name__)

class TextToImageGenerator:
    """文字转图片生成器"""
    
    def __init__(self):
        self.default_font_path = self._get_font_path()
        self.max_width = 800
        self.line_height = 30
        self.padding = 40
        self.bg_color = (255, 255, 255)
        self.text_color = (0, 0, 0)
    
    def _get_font_path(self):
        """获取系统字体路径"""
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
            '/System/Library/Fonts/Arial.ttf',  # macOS
            'C:/Windows/Fonts/arial.ttf',  # Windows
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                return path
        
        # 如果找不到字体，使用默认字体
        return None
    
    def generate_summary_image(self, summary_data, template_type='图文纪要'):
        """
        生成会议纪要图片
        
        Args:
            summary_data: 纪要数据字典
            template_type: 模板类型
            
        Returns:
            bytes: 图片的二进制数据
        """
        try:
            if template_type == '图文纪要':
                return self._generate_graphic_summary(summary_data)
            elif template_type == '会议纪要':
                return self._generate_simple_summary(summary_data)
            else:
                return self._generate_simple_summary(summary_data)
        except Exception as e:
            logger.error(f"生成纪要图片失败: {str(e)}")
            # 返回错误图片
            return self._generate_error_image(str(e))
    
    def _generate_graphic_summary(self, summary_data):
        """生成图文纪要图片"""
        # 创建画布
        width = 1000
        height = 1200
        image = Image.new('RGB', (width, height), self.bg_color)
        draw = ImageDraw.Draw(image)
        
        try:
            # 加载字体
            font_title = self._get_font(32)
            font_header = self._get_font(24)
            font_text = self._get_font(18)
            font_small = self._get_font(14)
        except:
            font_title = None
            font_header = None
            font_text = None
            font_small = None
        
        # 绘制标题
        title = summary_data.get('title', '会议纪要')
        self._draw_text(draw, title, font_title, (50, 50), fill=(52, 152, 219))
        
        # 绘制分割线
        draw.line([(50, 100), (950, 100)], fill=(52, 152, 219), width=2)
        
        # 绘制基本信息
        y_offset = 130
        info_items = [
            f"仓库: {summary_data.get('repository', 'N/A')}",
            f"会议时间: {summary_data.get('meeting_date', 'N/A')}",
            f"参会人员: {summary_data.get('participants', 'N/A')}",
            f"生成时间: {summary_data.get('generated_at', 'N/A')}"
        ]
        
        for info in info_items:
            self._draw_text(draw, info, font_text, (70, y_offset))
            y_offset += 35
        
        # 绘制会议摘要
        y_offset += 20
        self._draw_text(draw, "会议摘要", font_header, (70, y_offset), fill=(41, 128, 185))
        y_offset += 40
        
        summary_text = summary_data.get('summary_text', '')
        if summary_text:
            lines = self._wrap_text(summary_text, font_text, 800)
            for line in lines:
                self._draw_text(draw, line, font_text, (70, y_offset))
                y_offset += 25
                if y_offset > 800:  # 防止超出画布
                    break
        
        # 绘制讨论要点
        y_offset += 20
        self._draw_text(draw, "讨论要点", font_header, (70, y_offset), fill=(41, 128, 185))
        y_offset += 40
        
        key_points = summary_data.get('key_points', [])
        for point in key_points[:8]:  # 限制显示数量
            self._draw_text(draw, f"• {point}", font_text, (90, y_offset))
            y_offset += 25
            if y_offset > 800:
                break
        
        # 绘制决策事项
        decisions = summary_data.get('decisions', [])
        if decisions:
            y_offset += 20
            self._draw_text(draw, "决策事项", font_header, (70, y_offset), fill=(41, 128, 185))
            y_offset += 40
            
            for decision in decisions[:5]:  # 限制显示数量
                self._draw_text(draw, f"✅ {decision}", font_text, (90, y_offset))
                y_offset += 25
                if y_offset > 800:
                    break
        
        # 绘制待办任务表格
        action_items = summary_data.get('action_items', [])
        if action_items:
            y_offset += 20
            self._draw_text(draw, "待办任务", font_header, (70, y_offset), fill=(41, 128, 185))
            y_offset += 40
            
            # 绘制表头
            draw.rectangle([(70, y_offset), (930, y_offset + 30)], fill=(52, 152, 219))
            self._draw_text(draw, "任务", font_small, (80, y_offset + 5), fill=(255, 255, 255))
            self._draw_text(draw, "负责人", font_small, (400, y_offset + 5), fill=(255, 255, 255))
            self._draw_text(draw, "截止时间", font_small, (700, y_offset + 5), fill=(255, 255, 255))
            
            y_offset += 35
            
            for item in action_items[:4]:  # 限制显示数量
                task = item.get('task', '')[:50] + '...' if len(item.get('task', '')) > 50 else item.get('task', '')
                assignee = item.get('assignee', '')[:15]
                deadline = item.get('deadline', '')[:10]
                
                draw.rectangle([(70, y_offset), (930, y_offset + 30)], fill=(240, 240, 240))
                self._draw_text(draw, task, font_text, (80, y_offset + 5))
                self._draw_text(draw, assignee, font_text, (400, y_offset + 5))
                self._draw_text(draw, deadline, font_text, (700, y_offset + 5))
                
                y_offset += 35
        
        # 添加底部信息
        y_offset = height - 40
        footer_text = "Generated by 熵减X-AI"
        self._draw_text(draw, footer_text, font_small, (width - len(footer_text) * 8, y_offset), 
                       fill=(149, 165, 166))
        
        # 转换为字节流
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
    def _generate_simple_summary(self, summary_data):
        """生成简单纪要图片"""
        # 使用matplotlib生成
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']  # 支持中文
        plt.rcParams['axes.unicode_minus'] = False
        
        fig, ax = plt.subplots(figsize=(12, 16))
        ax.axis('off')
        
        # 创建数据
        content = self._build_summary_content(summary_data)
        
        # 显示文本
        ax.text(0.05, 0.95, content, transform=ax.transAxes, fontsize=12, 
                verticalalignment='top', fontfamily='sans-serif',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # 调整布局
        plt.tight_layout()
        
        # 转换为字节流
        img_byte_arr = BytesIO()
        plt.savefig(img_byte_arr, format='png', dpi=150, bbox_inches='tight')
        img_byte_arr.seek(0)
        plt.close()
        
        return img_byte_arr.getvalue()
    
    def _build_summary_content(self, summary_data):
        """构建纪要内容字符串"""
        content = f"""
会议纪要
========

标题: {summary_data.get('title', 'N/A')}

基本信息:
- 仓库: {summary_data.get('repository', 'N/A')}
- 会议时间: {summary_data.get('meeting_date', 'N/A')}
- 参会人员: {summary_data.get('participants', 'N/A')}
- 生成时间: {summary_data.get('generated_at', 'N/A')}

会议摘要:
{summary_data.get('summary_text', 'N/A')}

讨论要点:
"""
        
        for i, point in enumerate(summary_data.get('key_points', [])[:10], 1):
            content += f"{i}. {point}\n"
        
        if summary_data.get('decisions'):
            content += "\n决策事项:\n"
            for i, decision in enumerate(summary_data.get('decisions')[:5], 1):
                content += f"{i}. ✅ {decision}\n"
        
        if summary_data.get('action_items'):
            content += "\n待办任务:\n"
            for i, item in enumerate(summary_data.get('action_items')[:5], 1):
                task = item.get('task', '')[:30] + '...' if len(item.get('task', '')) > 30 else item.get('task', '')
                content += f"{i}. {task}\n"
        
        return content
    
    def _draw_text(self, draw, text, font, position, fill=None):
        """绘制文本"""
        if fill is None:
            fill = self.text_color
        
        if font:
            try:
                draw.text(position, text, font=font, fill=fill)
            except:
                # 如果字体加载失败，使用默认方式
                draw.text(position, text, fill=fill)
        else:
            draw.text(position, text, fill=fill)
    
    def _get_font(self, size):
        """获取字体"""
        if self.default_font_path:
            try:
                return ImageFont.truetype(self.default_font_path, size)
            except:
                pass
        
        # 尝试使用matplotlib字体
        try:
            return ImageFont.load_default()
        except:
            return None
    
    def _wrap_text(self, text, font, max_width):
        """自动换行文本"""
        lines = []
        current_line = ""
        
        for char in text:
            if char == '\n':
                lines.append(current_line)
                current_line = ""
            else:
                test_line = current_line + char
                # 这里简化处理，实际应该使用PIL的文本宽度计算
                if len(test_line) * 10 > max_width:  # 简化的宽度计算
                    lines.append(current_line)
                    current_line = char
                else:
                    current_line = test_line
        
        if current_line:
            lines.append(current_line)
        
        return lines[:10]  # 限制行数
    
    def _generate_error_image(self, error_msg):
        """生成错误提示图片"""
        image = Image.new('RGB', (800, 200), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        try:
            font = self._get_font(20)
        except:
            font = None
        
        draw.text((50, 50), "生成图片失败", font=font, fill=(255, 0, 0))
        draw.text((50, 80), error_msg, font=font, fill=(0, 0, 0))
        
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()

# 全局实例
image_generator = TextToImageGenerator()