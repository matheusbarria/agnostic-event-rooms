import socket
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import statistics
import matplotlib.pyplot as plt
from collections import defaultdict
concurrent_rooms = 7
class MatchmakerTester:
    def __init__(self, host='127.0.0.1', matchmaker_port=5050):
        self.host = host
        self.matchmaker_port = matchmaker_port
        self.creation_times = defaultdict(list)
        self.error_count = 0
        self.created_rooms = defaultdict(list)
        
    def create_room(self, app_type):
        app_numbers = {
            "connect4": "2",
            "drawing_board": "3",
            "chat": "1"
        }
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            start_time = time.time()
            
            sock.connect((self.host, self.matchmaker_port))
            request = (
                f"POST / HTTP/1.1\r\n"
                f"Host: {self.host}:{self.matchmaker_port}\r\n"
                f"Content-Type: application/x-www-form-urlencoded\r\n"
                f"Content-Length: {len(f'appNum={app_numbers[app_type]}')}\r\n"
                f"\r\n"
                f"appNum={app_numbers[app_type]}"
            )
            sock.send(request.encode())
            
            response = sock.recv(4096).decode()
            
            end_time = time.time()
            creation_time = end_time - start_time
            
            port = None
            for line in response.split('\n'):
                if 'Location:' in line:
                    try:
                        port = int(line.split(':')[-1].strip())
                        break
                    except ValueError:
                        pass
            
            if port:
                self.creation_times[app_type].append(creation_time)
                self.created_rooms[app_type].append(port)
                return port, creation_time
            else:
                self.error_count += 1
                return None, creation_time
                
        except Exception as e:
            print(f"Error creating room: {e}")
            self.error_count += 1
            return None, 0
        finally:
            sock.close()

    def run_concurrent_test(self, app_type, num_concurrent, delay_between_groups=1.5):
        print(f"\nTesting concurrent room creation for {app_type}")
        print(f"Creating {num_concurrent} rooms simultaneously")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [
                executor.submit(self.create_room, app_type)
                for _ in range(num_concurrent)
            ]
            
            results = []
            for future in futures:
                try:
                    result = future.result()
                    if result[0]:  
                        results.append(result)
                except Exception as e:
                    print(f"Error in concurrent creation: {e}")
                    self.error_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        success_rate = len(results) / num_concurrent * 100
        
        print(f"Results for {app_type}:")
        print(f"- Total time for all rooms: {total_time:.2f} seconds")
        print(f"- Average creation time: {statistics.mean(self.creation_times[app_type]):.3f} seconds")
        print(f"- Success rate: {success_rate:.1f}%")
        print(f"- Errors: {self.error_count}")
        
        # Give matchmaker time to clean up before next batch
        time.sleep(delay_between_groups)
        
        return {
            'app_type': app_type,
            'total_time': total_time,
            'avg_creation_time': statistics.mean(self.creation_times[app_type]),
            'success_rate': success_rate,
            'errors': self.error_count
        }

    def plot_results(self, results):
        """Create visualizations of the test results"""
        if not self.creation_times:
            print("No data to plot")
            return
            
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        creation_data = []
        labels = []
        for app_type in self.creation_times:
            if self.creation_times[app_type]:
                creation_data.append(self.creation_times[app_type])
                labels.append(app_type)
        
        if creation_data:
            ax1.boxplot(creation_data, labels=labels)
            ax1.set_title('Room Creation Time Distribution')
            ax1.set_ylabel('Seconds')
            
        apps = [r['app_type'] for r in results]
        success_rates = [r['success_rate'] for r in results]
        ax2.bar(apps, success_rates)
        ax2.set_title('Room Creation Success Rate')
        ax2.set_ylabel('Success Rate (%)')
        
        # Plot 3: Port allocation patterns
        for app_type in self.created_rooms:
            if self.created_rooms[app_type]:
                ax3.scatter([app_type] * len(self.created_rooms[app_type]), 
                          self.created_rooms[app_type],
                          alpha=0.5)
        ax3.set_title('Port Allocation Pattern')
        ax3.set_ylabel('Allocated Port')
        
        for app_type in self.creation_times:
            times = self.creation_times[app_type]
            ax4.plot(range(1, len(times) + 1), times, label=app_type, marker='o')
        ax4.set_title('Creation Time vs Request Order')
        ax4.set_xlabel('Request Number')
        ax4.set_ylabel('Creation Time (s)')
        ax4.legend()
        
        plt.tight_layout()
        plt.savefig(f'results/matchmaker_test_results{concurrent_rooms}.png')
        plt.close()

def main():
    tester = MatchmakerTester(matchmaker_port=5050)
    
    test_configs = [
        {'app_type': 'connect4', 'concurrent': concurrent_rooms},
        {'app_type': 'drawing_board', 'concurrent': concurrent_rooms},
        {'app_type': 'chat', 'concurrent': concurrent_rooms}
    ]
    
    results = []
    for config in test_configs:
        result = tester.run_concurrent_test(
            config['app_type'],
            config['concurrent']
        )
        results.append(result)
        time.sleep(1.5) 
    
    tester.plot_results(results)
    
    print("\nOverall Test Summary:")
    for result in results:
        print(f"\n{result['app_type']}:")
        print(f"- Average room creation time: {result['avg_creation_time']*1000:.2f} ms")
        print(f"- Success rate: {result['success_rate']:.1f}%")
        print(f"- Total errors: {result['errors']}")

if __name__ == "__main__":
    main()