import socket
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt
num_clients = 10
reqs = 10

class HTTPLoadTester:
    def __init__(self, host='127.0.0.1', matchmaker_port=5050):
        self.host = host
        self.matchmaker_port = matchmaker_port
        self.latencies = defaultdict(list)
        self.error_count = 0
        
    def send_http_request(self, port, method="GET", path="/", data=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            start_time = time.time()
            sock.connect((self.host, port))
            
            request = f"{method} {path} HTTP/1.1\r\n"
            request += f"Host: {self.host}:{port}\r\n"
            
            if data:
                request += "Content-Type: application/x-www-form-urlencoded\r\n"
                request += f"Content-Length: {len(data)}\r\n"
                request += "\r\n"
                request += data
            else:
                request += "\r\n"
            sock.send(request.encode())
            
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                
            end_time = time.time()
            latency = end_time - start_time
            
            return response.decode(), latency
            
        except Exception as e:
            print(f"Error in HTTP request: {e}")
            self.error_count += 1
            return None, 0
        finally:
            sock.close()

    def create_room(self, app_type):
        # Map app type to app number
        app_numbers = {
            "connect4": "2",
            "drawing_board": "3",
            "chat": "1"
        }
        app_num = app_numbers[app_type]
        
        try:
            response, _ = self.send_http_request(
                self.matchmaker_port, 
                "POST", 
                "/", 
                f"appNum={app_num}"
            )
            
            if response:
                for line in response.split('\n'):
                    if 'Location:' in line:
                        return int(line.split(':')[-1].strip())
            return None
        except Exception as e:
            print(f"Error creating room: {e}")
            return None

    def simulate_client(self, port, num_requests, app_type):
        for i in range(num_requests):
            if i % 3 == 0: 
                data = self.generate_test_data(app_type, i)
                response, latency = self.send_http_request(port, "POST", "/", data)
            else:
                response, latency = self.send_http_request(port)
                
            if response:
                self.latencies[app_type].append(latency)
            time.sleep(0.5)

    def generate_test_data(self, app_type, request_num):
        if app_type == "connect4":
            column = (request_num % 7) + 1
            return f"client=test_client&message={column}"
        elif app_type == "drawing_board":
            x = (request_num * 10) % 500
            y = (request_num * 20) % 500
            return f"client={x},{y},#FF0000"
        else:  # chat
            return f"client=test_client&message=test_message_{request_num}"

    def run_load_test(self, app_type, num_clients, requests_per_client):
        print(f"\nCreating room for {app_type}")
        room_port = self.create_room(app_type)
        
        if not room_port:
            print(f"Failed to create room for {app_type}")
            return None
            
        print(f"Room created on port {room_port}")
        time.sleep(1)  # Allow room to initialize
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = [
                executor.submit(self.simulate_client, room_port, requests_per_client, app_type)
                for _ in range(num_clients)
            ]
            
            for future in futures:
                future.result()
                
        end_time = time.time()
        
        total_time = end_time - start_time
        total_requests = num_clients * requests_per_client
        throughput = total_requests / total_time if total_time > 0 else 0
        avg_latency = statistics.mean(self.latencies[app_type]) if self.latencies[app_type] else 0
        
        return {
            'app_type': app_type,
            'port': room_port,
            'total_time': total_time,
            'throughput': throughput,
            'avg_latency': avg_latency,
            'errors': self.error_count
        }

    def plot_results(self, results):
        if not results:
            print("No data to plot")
            return
            
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Plot latencies for each application
        latency_data = []
        labels = []
        for app_type in self.latencies:
            if self.latencies[app_type]:
                latency_data.append(self.latencies[app_type])
                labels.append(app_type)
        
        if latency_data:
            ax1.boxplot(latency_data, labels=labels)
            ax1.set_title('Latency Distribution')
            ax1.set_ylabel('Seconds')
            
        # Plot throughput
        apps = [r['app_type'] for r in results]
        throughputs = [r['throughput'] for r in results]
        ax2.bar(apps, throughputs)
        ax2.set_title('Throughput')
        ax2.set_ylabel('Requests per Second')
        
        plt.tight_layout()
        plt.savefig(f'results/load_test_results{num_clients}-{reqs}.png')
        plt.close()

def main():
    tester = HTTPLoadTester(matchmaker_port=5050)
    
    test_configs = [
        {'app_type': 'connect4', 'num_clients': num_clients, 'requests': reqs},
        {'app_type': 'drawing_board', 'num_clients': num_clients, 'requests': reqs},
        {'app_type': 'chat', 'num_clients': num_clients, 'requests': reqs}
    ]
    
    results = []
    for config in test_configs:
        print(f"\nTesting {config['app_type']} application")
        result = tester.run_load_test(
            config['app_type'],
            config['num_clients'],
            config['requests']
        )
        if result:
            results.append(result)
            print(f"Results for {config['app_type']}:")
            print(f"- Total time: {result['total_time']:.2f} seconds")
            print(f"- Throughput: {result['throughput']:.2f} requests/second")
            print(f"- Average latency: {result['avg_latency']*1000:.2f} ms")
            print(f"- Errors: {result['errors']}")
    
    tester.plot_results(results)

if __name__ == "__main__":
    main()