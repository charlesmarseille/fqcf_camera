#include <libcamera/libcamera.h>
#include <libcamera/camera_manager.h>
#include <libcamera/framebuffer_allocator.h>
#include <libcamera/request.h>
#include <libcamera/stream.h>
#include <iostream>
#include <fstream>
#include <memory>
#include <vector>
#include <sys/mman.h>
#include <atomic>
#include <condition_variable>
#include <mutex>

std::atomic<bool> request_completed(false);
std::condition_variable cv;
std::mutex mtx;

void requestComplete(libcamera::Request *request) {
    std::lock_guard<std::mutex> lock(mtx);
    request_completed = true;
    cv.notify_one();
}

int main() {
    libcamera::CameraManager manager;
    manager.start();

    std::vector<std::shared_ptr<libcamera::Camera>> cameras = manager.cameras();
    if (cameras.empty()) {
        std::cerr << "No cameras found" << std::endl;
        return -1;
    }

    std::shared_ptr<libcamera::Camera> camera = cameras.front();
    camera->acquire();

    std::unique_ptr<libcamera::CameraConfiguration> config = camera->generateConfiguration({libcamera::StreamRole::StillCapture});
    if (config->validate() != libcamera::CameraConfiguration::Valid) {
        std::cerr << "Invalid camera configuration" << std::endl;
        return -1;
    }

    if (camera->configure(config.get()) < 0) {
        std::cerr << "Failed to configure camera" << std::endl;
        return -1;
    }

    libcamera::Stream *stream = config->at(0).stream();

    libcamera::FrameBufferAllocator allocator(camera);
    if (allocator.allocate(stream) < 0) {
        std::cerr << "Failed to allocate buffers" << std::endl;
        return -1;
    }

    std::vector<std::unique_ptr<libcamera::Request>> requests;
    for (const std::unique_ptr<libcamera::FrameBuffer> &buffer : allocator.buffers(stream)) {
        std::unique_ptr<libcamera::Request> request = camera->createRequest();
        if (!request) {
            std::cerr << "Failed to create request" << std::endl;
            return -1;
        }
        if (request->addBuffer(stream, buffer.get()) < 0) {
            std::cerr << "Failed to add buffer to request" << std::endl;
            return -1;
        }
        requests.push_back(std::move(request));
    }

    camera->requestCompleted.connect(requestComplete);

    if (camera->start() < 0) {
        std::cerr << "Failed to start camera" << std::endl;
        return -1;
    }

    for (std::unique_ptr<libcamera::Request> &request : requests) {
        if (camera->queueRequest(request.get()) < 0) {
            std::cerr << "Failed to queue request" << std::endl;
            return -1;
        }
    }

    // Capture loop (Example: Capture 3 images)
    for (int i = 0; i < 3; ++i) {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [] { return request_completed.load(); });
        request_completed = false;

        libcamera::Request *completedRequest = requests[i % requests.size()].get();
        libcamera::FrameBuffer *buffer = completedRequest->findBuffer(stream);
        if (!buffer) {
            std::cerr << "Could not find buffer" << std::endl;
            break;
        }

        // Process the captured image (Example: save to a file)
        std::ofstream outputFile("capture_" + std::to_string(i) + ".raw", std::ios::binary); // Save as raw for simplicity
        if (outputFile) {
            void *mapped_buffer = mmap(NULL, buffer->planes()[0].length, PROT_READ, MAP_SHARED, buffer->planes()[0].fd.get(), 0);
            outputFile.write(static_cast<char *>(mapped_buffer), buffer->planes()[0].length);
            munmap(mapped_buffer, buffer->planes()[0].length);
            outputFile.close();
            std::cout << "Captured image " << i + 1 << std::endl;
        } else {
            std::cerr << "Error opening output file" << std::endl;
        }

        // Reset the request before re-queuing it
        completedRequest->reuse();
        if (completedRequest->addBuffer(stream, buffer) < 0) {
            std::cerr << "Failed to add buffer to request" << std::endl;
            return -1;
        }

        // Re-queue the completed request
        if (camera->queueRequest(completedRequest) < 0) {
            std::cerr << "Failed to re-queue request" << std::endl;
            return -1;
        }
    }

    // Stop the camera
    camera->stop();
    allocator.free(stream);
    camera->release();
    manager.stop();

    return 0;
}