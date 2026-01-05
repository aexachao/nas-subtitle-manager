#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
媒体扫描服务
负责扫描媒体目录并发现字幕文件
"""

import os
from pathlib import Path
from typing import List, Tuple, Optional

from core.models import SubtitleInfo, SUPPORTED_VIDEO_EXTENSIONS
from database.media_dao import MediaDAO
from utils.lang_detection import detect_language_combined


# 默认媒体根目录
MEDIA_ROOT = "/media"


class MediaScanner:
    """媒体扫描器"""
    
    def __init__(self, media_root: str = MEDIA_ROOT):
        """
        初始化扫描器
        
        Args:
            media_root: 媒体根目录
        """
        self.media_root = Path(media_root)
    
    def discover_subdirectories(self, max_depth: int = 3) -> List[str]:
        """
        发现媒体根目录下的所有子目录
        
        Args:
            max_depth: 最大扫描深度
        
        Returns:
            相对路径列表（如 ["Movies/Action", "TV Shows/Drama"]）
        """
        if not self.media_root.exists():
            return []
        
        subdirs = []
        
        try:
            # 使用广度优先搜索，避免递归过深
            to_scan = [(self.media_root, 0)]  # (路径, 深度)
            
            while to_scan:
                current_dir, depth = to_scan.pop(0)
                
                if depth >= max_depth:
                    continue
                
                try:
                    for item in current_dir.iterdir():
                        if item.is_dir() and not item.name.startswith('.'):
                            # 计算相对路径
                            rel_path = str(item.relative_to(self.media_root))
                            subdirs.append(rel_path)
                            
                            # 继续扫描下一层
                            if depth + 1 < max_depth:
                                to_scan.append((item, depth + 1))
                except PermissionError:
                    continue
        
        except Exception as e:
            print(f"[MediaScanner] Failed to discover subdirectories: {e}")
        
        return sorted(subdirs)
    
    def scan_directory(
        self, 
        subdirectory: Optional[str] = None,
        debug: bool = False
    ) -> Tuple[int, List[str]]:
        """
        扫描媒体目录
        
        Args:
            subdirectory: 子目录相对路径（None=扫描全部）
            debug: 是否输出调试日志
        
        Returns:
            (新增文件数, 调试日志列表)
        """
        # 确定扫描路径
        if subdirectory:
            scan_path = self.media_root / subdirectory
            if not scan_path.exists():
                return 0, [f"子目录不存在: {subdirectory}"]
        else:
            scan_path = self.media_root
        
        if not scan_path.exists():
            return 0, [f"路径不存在: {scan_path}"]
        
        added_count = 0
        debug_logs = []
        batch_data = []
        
        if debug:
            debug_logs.append(f"📂 扫描目录: {scan_path}")
        
        try:
            # 遍历目录
            for root, dirs, files in os.walk(scan_path):
                for file in files:
                    file_path = Path(root) / file
                    
                    # 检查是否为支持的视频格式
                    if file_path.suffix.lower() not in SUPPORTED_VIDEO_EXTENSIONS:
                        continue
                    
                    try:
                        # 扫描字幕文件
                        subtitles = self._scan_subtitles_for_video(file_path)
                        
                        # 检查是否有翻译
                        has_translated = self._check_has_translation(subtitles)
                        
                        # 准备批量插入数据
                        import json
                        subtitles_json = json.dumps(
                            [s.to_dict() for s in subtitles],
                            ensure_ascii=False
                        )
                        
                        batch_data.append((
                            str(file_path),
                            file,
                            file_path.stat().st_size,
                            subtitles_json,
                            int(has_translated)
                        ))
                        
                        added_count += 1
                        
                        if debug:
                            debug_logs.append(f"✓ 发现: {file}")
                    
                    except Exception as e:
                        if debug:
                            debug_logs.append(f"✗ 错误 {file}: {e}")
            
            # 批量写入数据库
            if batch_data:
                MediaDAO.batch_add_or_update_media_files(batch_data)
                if debug:
                    debug_logs.append(f"✓ 批量写入 {len(batch_data)} 条记录")
        
        except Exception as e:
            print(f"[MediaScanner] Scan failed: {e}")
            if debug:
                debug_logs.append(f"✗ 扫描失败: {e}")
        
        return added_count, debug_logs
    
    def _scan_subtitles_for_video(self, video_path: Path) -> List[SubtitleInfo]:
        """
        扫描视频文件对应的字幕
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            字幕信息列表
        """
        subtitles = []
        base_name = video_path.stem
        parent_dir = video_path.parent
        
        try:
            # 查找同名的 SRT 文件
            all_files = list(parent_dir.iterdir())
            
            potential_subs = [
                p for p in all_files
                if p.is_file()
                and p.name.lower().endswith('.srt')
                and p.name.lower().startswith(base_name.lower())
            ]
            
            for sub_path in potential_subs:
                sub_name = sub_path.name
                
                # 检测语言
                lang_code, tag = detect_language_combined(
                    str(sub_path),
                    sub_name
                )
                
                # 检查是否为默认字幕
                if sub_path.stem.lower() == base_name.lower():
                    tag += " (默认)"
                
                subtitles.append(SubtitleInfo(
                    path=str(sub_path),
                    lang=lang_code,
                    tag=tag
                ))
        
        except Exception as e:
            print(f"[MediaScanner] Failed to scan subtitles for {video_path}: {e}")
        
        return subtitles
    
    def _check_has_translation(self, subtitles: List[SubtitleInfo]) -> bool:
        """
        检查是否有中文翻译字幕
        
        Args:
            subtitles: 字幕列表
        
        Returns:
            是否有翻译
        """
        for sub in subtitles:
            if sub.lang.lower() in ['zh', 'chs', 'cht']:
                return True
        return False
    
    def rescan_single_video(self, video_path: str):
        """
        重新扫描单个视频文件的字幕
        
        Args:
            video_path: 视频文件路径
        """
        path = Path(video_path)
        
        if not path.exists():
            print(f"[MediaScanner] Video not found: {video_path}")
            return
        
        subtitles = self._scan_subtitles_for_video(path)
        has_translated = self._check_has_translation(subtitles)
        
        MediaDAO.update_media_subtitles(video_path, subtitles, has_translated)


# ============================================================================
# 快捷函数
# ============================================================================

def scan_media_directory(
    directory: str = MEDIA_ROOT,
    subdirectory: Optional[str] = None,
    debug: bool = False
) -> Tuple[int, List[str]]:
    """
    扫描媒体目录（快捷函数）
    
    Args:
        directory: 媒体目录路径
        subdirectory: 子目录相对路径（None=扫描全部）
        debug: 是否输出调试日志
    
    Returns:
        (新增文件数, 调试日志列表)
    """
    scanner = MediaScanner(directory)
    return scanner.scan_directory(subdirectory, debug)


def discover_media_subdirectories(
    directory: str = MEDIA_ROOT,
    max_depth: int = 2
) -> List[str]:
    """
    发现媒体子目录（快捷函数）
    
    Args:
        directory: 媒体目录路径
        max_depth: 最大扫描深度
    
    Returns:
        子目录列表
    """
    scanner = MediaScanner(directory)
    return scanner.discover_subdirectories(max_depth)


def rescan_video_subtitles(video_path: str):
    """
    重新扫描视频字幕（快捷函数）
    
    Args:
        video_path: 视频文件路径
    """
    scanner = MediaScanner()
    scanner.rescan_single_video(video_path)