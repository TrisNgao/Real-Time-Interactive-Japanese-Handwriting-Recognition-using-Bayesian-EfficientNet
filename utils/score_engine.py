def cham_diem(target_char, results):
    """
    target_char : chữ đúng cần viết
    results     : list top-k từ model [{'char':..., 'prob':...}]
    returns     : dict {score, nhan_xet, color}
    """
    if not results:
        return {'score': 0, 'nhan_xet': '❌ Không nhận dạng được', 'color': 'red'}

    top1_char = results[0]['char']
    top1_prob = results[0]['prob']

    # Tính score
    if top1_char == target_char:
        score = top1_prob
    else:
        score = 0
        for r in results:
            if r['char'] == target_char:
                score = r['prob'] * 0.5
                break

    # Nhận xét
    if score >= 0.9:
        return {
            'score'    : score,
            'nhan_xet' : f'🌟 Xuất sắc! Bạn viết đúng {target_char}',
            'color'    : 'green'
        }
    elif score >= 0.7:
        return {
            'score'    : score,
            'nhan_xet' : f'✅ Tốt lắm! Model nhận ra {top1_char}',
            'color'    : 'green'
        }
    elif score >= 0.4:
        return {
            'score'    : score,
            'nhan_xet' : f'⚠️  Gần đúng! Model thấy {top1_char}, cần viết {target_char}',
            'color'    : 'orange'
        }
    else:
        return {
            'score'    : score,
            'nhan_xet' : f'❌ Sai! Model thấy {top1_char}, bạn cần viết {target_char}',
            'color'    : 'red'
        }
