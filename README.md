# Dungeon Quest 

## 🎯 Mục đích học tập
Project này được xây dựng để:
- Thực hành **thuật toán BFS (Breadth-First Search)** để tìm đường đi ngắn nhất
- Áp dụng **DFS** trong xử lý đồ thị (map generation)
- Rèn luyện tư duy logic và Python OOP

## 🧠 Thuật toán nổi bật
- BFS (Breadth-First Search): Tìm đường đi ngắn nhất
- DFS (Depth-First Search): Tạo map ngẫu nhiên
- `bfs_move()`: Tìm đường đi cho quái vật từ vị trí hiện tại đến người chơi
- `check_path()`: Kiểm tra xem có đường đi từ A đến B không (dùng BFS)
- Map generation: Sử dụng thuật toán đào hang (stack-based) - tương tự DFS

## 📚 Kỹ năng thể hiện
- Python, Pygame
- Xử lý sự kiện bất đồng bộ (asyncio)
- Thiết kế game đa nền tảng (touch + keyboard)
- Quản lý âm thanh, animation, collision detection

Điều khiển
WASD: Di chuyển
SPACE: Tấn công
Q: Dash
E: Spin attack
R: Ultimate (khi đủ 10 kill)

Tính năng
4 cấp độ
4 loại quái vật
Boss với skill bắn đạn
Hỗ trợ touch và keyboard
