require 'json'

module Jekyll
  class HeritagePageGenerator < Generator
    safe true
    priority :normal

    def generate(site)
      items = load_json(site, '_rawdata/heritage.json')

      Jekyll.logger.info "HeritageGenerator:", "#{items.size}개 향토유산 페이지 생성 중..."
      items.each do |h|
        next if h['slug'].to_s.strip.empty?
        site.pages << HeritagePage.new(site, h)
      end

      Jekyll.logger.info "HeritageGenerator:", "완료 (#{items.size}개)"
    end

    private

    def load_json(site, path)
      file = File.join(site.source, path)
      return [] unless File.exist?(file)
      JSON.parse(File.read(file, encoding: 'utf-8'))
    rescue => e
      Jekyll.logger.warn "HeritageGenerator:", "#{path} 로드 실패: #{e.message}"
      []
    end
  end

  class HeritagePage < Page
    def initialize(site, h)
      @site = site
      @base = site.source
      @dir  = "heritage/#{h['slug']}"
      @name = 'index.html'

      self.process(@name)
      self.read_yaml(File.join(@base, '_layouts'), 'heritage.html')
      self.data.merge!(h)
      self.data['layout']      = 'heritage'
      self.data['title']       = build_title(h)
      self.data['description'] = build_desc(h)
    end

    private

    def build_title(h)
      loc = [h['doShort'], h['sigungu']].compact.join(' ')
      "#{h['heritageName']} #{loc} 위치 소개"
    end

    def build_desc(h)
      loc = [h['doShort'], h['sigungu']].compact.join(' ')
      intro = (h['intro'] || '').gsub(/\s+/, ' ')
      "#{loc} #{h['heritageName']}(#{h['type']}). #{intro}"[0, 155]
    end
  end
end
