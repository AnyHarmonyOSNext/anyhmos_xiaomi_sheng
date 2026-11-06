// 保存最近成功提交的层释放 fence，查询仅借用描述符
class DirectReleaseCache {
public:
    DirectReleaseCache() = default;
    DirectReleaseCache(const DirectReleaseCache &) = delete;
    DirectReleaseCache &operator=(const DirectReleaseCache &) = delete;
    ~DirectReleaseCache() { Reset(); }

    void Reset()
    {
        int old = fd_;
        fd_ = -1; layer_ = 0;
        if (old >= 0) close(old);
    }

    void Adopt(uint32_t layer, int fd)
    {
        Reset(); layer_ = layer; fd_ = fd;
    }

    void ResetLayer(uint32_t layer)
    {
        if (layer_ == layer) Reset();
    }

    int Borrow(uint32_t &layer) const
    {
        layer = layer_; return fd_;
    }

private:
    uint32_t layer_ = 0;
    int fd_ = -1;
};
