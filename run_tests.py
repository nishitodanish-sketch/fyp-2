import os
import time
import random

# Make sure this points to the folder you are monitoring!
WATCHED_FOLDER = "C:/Users/User/Documents/demo"

def test_1_false_positive_pdf():
    print("--- TEST 1: High Entropy PDF (False Positive Scenario) ---")
    print("Goal: Prove the system NO LONGER gets confused by normal PDFs.")
    
    path = os.path.join(WATCHED_FOLDER, "normal_presentation.pdf")
    
    # We generate 50,000 random bytes. This creates MAXIMUM entropy (randomness).
    # Before our fix, the AI would panic and quarantine this immediately.
    high_entropy_data = bytes([random.randint(0, 255) for _ in range(50000)])
    
    with open(path, "wb") as f:
        f.write(high_entropy_data)
        
    print(f"Created high-entropy file: {path}")
    print("EXPECTED RESULT in FIM: It should show up as NORMAL (Green) and NOT be quarantined.\n")
    time.sleep(4) # Wait to let the system process

def test_2_ransomware_simulation():
    print("--- TEST 2: Malicious Behavior (Rapid Modification) ---")
    print("Goal: Prove the system STILL catches actual ransomware attacks.")
    
    path = os.path.join(WATCHED_FOLDER, "important_financials.txt")
    
    # First, create a normal text file
    with open(path, "w") as f:
        f.write("This is a normal text file containing important data.")
    print(f"Created normal file: {path}")
    time.sleep(2)
    
    print("Simulating Ransomware: Rapidly encrypting the file in 0.2-second intervals...")
    # Now, rapidly overwrite it with random, high-entropy bytes (simulating encryption)
    for i in range(5):
        with open(path, "wb") as f:
            f.write(bytes([random.randint(0, 255) for _ in range(20000)]))
        time.sleep(0.2) # Rapid modification!
        
    print("EXPECTED RESULT in FIM: The system should detect the rapid modifications, flag it as CRITICAL, and immediately move it to the Quarantine tab.\n")

if __name__ == "__main__":
    os.makedirs(WATCHED_FOLDER, exist_ok=True)
    test_1_false_positive_pdf()
    test_2_ransomware_simulation()
    print("Tests finished! Check your FIM Dashboard, Live Events, and Quarantine tabs.")
