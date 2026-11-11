{
  virtualisation.memorySize = 4096;
  virtualisation.cores = 4;
  virtualisation.qemu.options = [ "-vga none -device virtio-gpu-pci" ];
  hardware.graphics.enable = true;
}
